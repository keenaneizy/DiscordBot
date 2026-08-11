"""
ServerSetup cog
────────────────
Builds and maintains the entire Phantom Picks server structure: categories,
channels, roles, channel permissions, and the pinned welcome / unit-sizing /
model-record messages.

provision_guild() runs automatically once per guild every time the bot
starts (see on_ready in bot.py), and can also be re-run any time with the
!setup command. It is fully idempotent: re-running it looks up existing
categories/channels/roles by name and updates them in place rather than
creating duplicates, so it's safe to run after manually tweaking something
or after the bot reconnects.
"""
import logging

import discord
from discord.ext import commands

import config
from checks import is_admin_or_owner
from data_store import DataStore
from formatting import build_welcome_message, build_unit_sizing_message, build_record_block

log = logging.getLogger("phantompicks.setup")


class ServerSetup(commands.Cog, name="ServerSetup"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = DataStore()

    # ── public entrypoint, called from bot.py's on_ready ────────────────
    async def provision_guild(self, guild: discord.Guild):
        log.info(f"Provisioning guild: {guild.name} ({guild.id})")

        free_role, vip_role = await self._ensure_roles(guild)
        channels = await self._ensure_categories_and_channels(guild, free_role, vip_role)
        await self._post_pinned_info_messages(channels)
        await self._backfill_free_role(guild, free_role)

        log.info(f"Provisioning complete for {guild.name}")

    # ── roles ────────────────────────────────────────────────────────────
    async def _ensure_roles(self, guild: discord.Guild):
        free_role = discord.utils.get(guild.roles, name=config.ROLE_FREE)
        if free_role is None:
            free_role = await guild.create_role(
                name=config.ROLE_FREE,
                reason="Phantom Picks setup: base community role",
                mentionable=False,
            )
            log.info("Created role: Free Member")

        vip_role = discord.utils.get(guild.roles, name=config.ROLE_VIP)
        if vip_role is None:
            vip_role = await guild.create_role(
                name=config.ROLE_VIP,
                reason="Phantom Picks setup: VIP role, membership managed externally by Winible",
                colour=discord.Colour.gold(),
                hoist=True,
                mentionable=False,
            )
            log.info("Created role: Phantom Pro")

        return free_role, vip_role

    # ── categories + channels ───────────────────────────────────────────
    async def _ensure_categories_and_channels(self, guild: discord.Guild, free_role, vip_role):
        everyone = guild.default_role

        # Read-only for everyone: only an admin (the owner) can post.
        # Used as-is for welcome/unit-sizing/model-record/free-daily-picks/free-results.
        readonly_overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True),
            free_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            vip_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        }

        # Open posting for everyone (free-chat, member-wins). Every target is
        # set explicitly so re-running !setup always converges to this state,
        # regardless of what overwrites a channel previously inherited.
        open_overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True),
            free_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            vip_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        # ── Category 1: INFORMATION ──
        info_cat = await self._ensure_category(guild, config.CAT_INFO, 0, readonly_overwrites)
        welcome_ch = await self._ensure_channel(guild, config.CH_WELCOME, info_cat, 0)
        unit_ch = await self._ensure_channel(guild, config.CH_UNIT_SIZING, info_cat, 1)

        # ── Category 2: MODEL RECORD ──
        record_cat = await self._ensure_category(guild, config.CAT_RECORD, 1, readonly_overwrites)
        record_ch = await self._ensure_channel(guild, config.CH_MODEL_RECORD, record_cat, 0)

        # ── Category 3: FREE PICKS ──
        free_cat = await self._ensure_category(guild, config.CAT_FREE, 2, readonly_overwrites)
        free_picks_ch = await self._ensure_channel(guild, config.CH_FREE_PICKS, free_cat, 0)
        free_results_ch = await self._ensure_channel(guild, config.CH_FREE_RESULTS, free_cat, 1)
        free_chat_ch = await self._ensure_channel(guild, config.CH_FREE_CHAT, free_cat, 2, open_overwrites)
        member_wins_ch = await self._ensure_channel(guild, config.CH_MEMBER_WINS, free_cat, 3, open_overwrites)

        # ── Category 4: VIP MEMBERS ONLY (invisible to Free Members) ──
        vip_overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            free_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            vip_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        }
        vip_cat = await self._ensure_category(guild, config.CAT_VIP, 3, vip_overwrites)
        vip_picks_ch = await self._ensure_channel(guild, config.CH_VIP_PICKS, vip_cat, 0)
        vip_results_ch = await self._ensure_channel(guild, config.CH_VIP_RESULTS, vip_cat, 1)

        vip_chat_overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            free_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            vip_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        vip_chat_ch = await self._ensure_channel(guild, config.CH_VIP_CHAT, vip_cat, 2, vip_chat_overwrites)

        return {
            "welcome": welcome_ch,
            "unit_sizing": unit_ch,
            "record": record_ch,
            "free_picks": free_picks_ch,
            "free_results": free_results_ch,
            "free_chat": free_chat_ch,
            "member_wins": member_wins_ch,
            "vip_picks": vip_picks_ch,
            "vip_results": vip_results_ch,
            "vip_chat": vip_chat_ch,
        }

    async def _ensure_category(self, guild: discord.Guild, name: str, position: int, overwrites: dict):
        category = discord.utils.get(guild.categories, name=name)
        if category is None:
            category = await guild.create_category(
                name, overwrites=overwrites, position=position, reason="Phantom Picks setup",
            )
            log.info(f"Created category: {name}")
        else:
            await category.edit(overwrites=overwrites, position=position)
        return category

    async def _ensure_channel(self, guild: discord.Guild, name: str, category: discord.CategoryChannel,
                               position: int, overwrites: dict | None = None):
        channel = discord.utils.get(category.text_channels, name=name)
        if channel is None:
            # discord.py's create_text_channel rejects overwrites=None outright
            # (it wants the kwarg omitted, not passed as None) — only include it
            # when we actually have channel-specific overwrites to apply. With no
            # explicit overwrites, a channel created under a category inherits
            # the category's permissions automatically.
            create_kwargs = {"category": category, "position": position, "reason": "Phantom Picks setup"}
            if overwrites is not None:
                create_kwargs["overwrites"] = overwrites
            channel = await guild.create_text_channel(name, **create_kwargs)
            log.info(f"Created channel: #{name}")
        else:
            if channel.category_id != category.id:
                await channel.edit(category=category)
            if overwrites is not None:
                await channel.edit(overwrites=overwrites)
            else:
                # No channel-specific overwrite requested: keep it fully
                # synced to the parent category's permissions.
                await channel.edit(sync_permissions=True)

        try:
            if channel.position != position:
                await channel.edit(position=position)
        except discord.HTTPException:
            # Position edits can occasionally race with Discord's own
            # normalization when many channels move at once; not worth failing setup over.
            pass

        return channel

    # ── pinned messages ──────────────────────────────────────────────────
    async def _post_pinned_info_messages(self, channels: dict):
        await self._sync_pinned_message(
            channels["welcome"], "pinned_welcome", build_welcome_message(),
            "Phantom Picks welcome message",
        )
        await self._sync_pinned_message(
            channels["unit_sizing"], "pinned_unit_sizing", build_unit_sizing_message(),
            "Phantom Picks responsible betting message",
        )
        await self.sync_record_pin(channels["record"])

    async def _sync_pinned_message(self, channel: discord.TextChannel, data_key: str,
                                    content: str, pin_reason: str):
        """Create (and pin) a message if one isn't already stored for this
        data_key, otherwise edit it in place — so editing the template in
        formatting.py actually updates the live message on the next
        startup/!setup, instead of only affecting brand-new servers.

        Also self-heals duplicates: if any *other* message authored by the
        bot is also pinned in this channel (e.g. a stale one left over from
        before this tracking existed, or from a data reset), it gets
        unpinned and deleted so there's only ever one."""
        data = self.store.load()
        pin_info = data.get(data_key, {})
        message = None

        if pin_info.get("message_id"):
            try:
                message = await channel.fetch_message(pin_info["message_id"])
            except (discord.NotFound, discord.HTTPException):
                message = None

        if message is None:
            message = await channel.send(content)
            try:
                await message.pin(reason=pin_reason)
            except discord.HTTPException:
                pass
            data[data_key] = {"channel_id": channel.id, "message_id": message.id}
            self.store.save(data)
            log.info(f"Posted + pinned {data_key}")
        else:
            await message.edit(content=content)

        try:
            pins = await channel.pins()
        except discord.HTTPException:
            pins = []
        for pinned in pins:
            if pinned.author.id == channel.guild.me.id and pinned.id != message.id:
                try:
                    await pinned.unpin(reason="Phantom Picks: removing duplicate pinned message")
                    await pinned.delete()
                    log.info(f"Removed duplicate pinned message in #{channel.name}")
                except discord.HTTPException:
                    pass

    async def sync_record_pin(self, record_channel: discord.TextChannel):
        """Create (and pin) the model record message if it doesn't exist yet,
        otherwise edit it in place. Called on startup and after every command
        that changes the record (!result, !updaterecord, !setrecord, !setunits)."""
        data = self.store.load()
        await self._sync_pinned_message(
            record_channel, "pinned_record", build_record_block(data),
            "Phantom Picks model record",
        )

    # ── backfill ─────────────────────────────────────────────────────────
    async def _backfill_free_role(self, guild: discord.Guild, free_role: discord.Role):
        """Give the Free Member role to any existing human member who
        doesn't already have it (new members get it automatically via
        on_member_join in cogs/welcome.py)."""
        for member in guild.members:
            if member.bot:
                continue
            if free_role not in member.roles:
                try:
                    await member.add_roles(free_role, reason="Phantom Picks setup: backfill base role")
                except discord.HTTPException:
                    log.warning(f"Could not add Free Member role to {member}")

    # ── manual re-run command ───────────────────────────────────────────
    @commands.command(name="setup")
    @is_admin_or_owner()
    @commands.guild_only()
    async def setup_command(self, ctx: commands.Context):
        """Re-run full server provisioning: categories, channels, roles,
        permissions, and pinned messages."""
        await ctx.send("👻 Re-running Phantom Picks setup...")
        await self.provision_guild(ctx.guild)
        await ctx.send("✅ Setup complete. Categories, channels, roles, and permissions are up to date.")

    @setup_command.error
    async def setup_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("🚫 Only the Phantom Picks admin can run `!setup`.")
        else:
            await ctx.send(f"⚠️ Setup failed: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerSetup(bot))
