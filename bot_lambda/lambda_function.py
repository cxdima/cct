# lambda_function.py

import os
import logging
import json
import asyncio
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ─── CONFIG & LOGGING ─────────────────────────────────────────────────────────
TOKEN       = os.getenv("TELEGRAM_TOKEN", "7818171562:REPLACE_ME")
TABLE_NAME  = os.getenv("DDB_TABLE", "cct-telegram-users")
REGION      = os.getenv("AWS_REGION", "us-east-1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── DYNAMODB REPOSITORY ──────────────────────────────────────────────────────
class Repository:
    def __init__(self, table_name: str, region: str):
        self._ddb   = boto3.resource("dynamodb", region_name=region)
        self._table = self._ddb.Table(table_name)

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            resp = self._table.get_item(Key={"user_id": user_id})
            return resp.get("Item")
        except Exception as e:
            logger.error("DDB get_item error: %s", e)
            return None

    def get_team(self, team_id: int) -> List[Dict[str, Any]]:
        resp = self._table.query(
            IndexName="team_id-index",
            KeyConditionExpression=Key("team_id").eq(team_id),
        )
        return resp.get("Items", [])

    def update_user(self, user_id: int, expr: str, vals: Dict[str, Any]) -> None:
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=expr,
            ExpressionAttributeValues=vals,
        )

    def buy_item(self, user_id: int, cost_gp: int, cost_money: int, new_item: Dict[str, Any]) -> bool:
        try:
            self._table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=(
                    "SET resources.gunpowder = resources.gunpowder - :gp, "
                    "resources.money     = resources.money - :m, "
                    "inventory           = list_append(if_not_exists(inventory, :empty), :itm)"
                ),
                ConditionExpression=(
                        Attr("resources.gunpowder").gte(cost_gp) &
                        Attr("resources.money").gte(cost_money)
                ),
                ExpressionAttributeValues={
                    ":gp": cost_gp,
                    ":m":  cost_money,
                    ":itm": [new_item],
                    ":empty": [],
                },
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            logger.error("DDB buy_item error: %s", e)
            return False

    def use_item(self, user_id: int, item_name: str) -> bool:
        # TODO: remove item & apply its effect atomically
        return True

    def scan_leaderboard(self) -> List[Dict[str, Any]]:
        resp = self._table.scan()
        tally: Dict[str, Decimal] = {}
        for itm in resp.get("Items", []):
            name = itm.get("team_name", "Unknown")
            pts  = Decimal(str(itm.get("win_points", 0)))
            tally[name] = tally.get(name, Decimal(0)) + pts
        return sorted(
            [{"team": t, "points": float(p)} for t, p in tally.items()],
            key=lambda x: -x["points"]
        )

repo = Repository(TABLE_NAME, REGION)

# ─── SHOP ITEMS ────────────────────────────────────────────────────────────────
SHOP_ITEMS = {
    "Pistol": {"description": "Grants +1 attack power.", "cost_gp": 1, "cost_money": 3},
    "Car":    {"description": "Grants +10 steps.",      "cost_gp": 0, "cost_money": 5},
}

# ─── HELPERS ───────────────────────────────────────────────────────────────────
async def smart_edit(query, text: str, keyboard: List[List[InlineKeyboardButton]]):
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await query.message.delete()
        await query.message.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

async def is_authorized(update: Update) -> (bool, Optional[Dict[str, Any]]):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user    = repo.get_user(user_id)
    if not user:
        return False, None
    if str(chat_id) != user.get("group_id"):
        return False, user
    return True, user

# ─── COMMAND HANDLERS ─────────────────────────────────────────────────────────
async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ok, user = await is_authorized(update)
    if not ok:
        msg = "❌ Not in DB." if not user else "❌ Wrong group."
        return await update.message.reply_text(msg)

    kb = [
        [InlineKeyboardButton("🛒 Shop",       callback_data="menu:shop"),
         InlineKeyboardButton("👥 Members",    callback_data="menu:members")],
        [InlineKeyboardButton("🗺️ Locations", callback_data="menu:locations"),
         InlineKeyboardButton("⚔️ Attack",     callback_data="menu:attack")],
        [InlineKeyboardButton("📦 Inventory",  callback_data="menu:inventory"),
         InlineKeyboardButton("🏆 Leaderboard", callback_data="menu:leaderboard")],
    ]
    await update.message.reply_text(
        f"🏠 Main Menu\nWelcome, *{user.get('username','')}*!",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def init_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = ctx.args
    if chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return await update.message.reply_text("❌ Must run in a group.")
    if not args or not args[0].isdigit():
        return await update.message.reply_text("⚠️ Usage: /init <team_id>")

    team_id = int(args[0])
    teams   = repo.get_team(team_id)
    if not teams:
        return await update.message.reply_text(f"❌ No team #{team_id}.")
    team = teams[0]
    if team.get("group_id"):
        return await update.message.reply_text(f"❌ Already linked to {team['group_id']}.")
    repo.update_user(int(team["user_id"]), "SET group_id = :g", {":g": str(chat.id)})
    await update.message.reply_text(
        f"✅ Linked team *{team['team_name']}* to this group.",
        parse_mode="Markdown"
    )

# ─── CALLBACK HANDLER ─────────────────────────────────────────────────────────
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ok, user = await is_authorized(update)
    q = update.callback_query
    if not ok:
        return await q.answer("❌ Unauthorized", show_alert=True)
    await q.answer()

    parts = q.data.split(":")
    cmd   = parts[0]
    args  = parts[1:]

    if cmd == "menu":
        menu = args[0]

        # ── Main Menu (now uses edit, not reply) ───────────────────────────
        if menu == "main":
            kb = [
                [InlineKeyboardButton("🛒 Shop",       callback_data="menu:shop"),
                 InlineKeyboardButton("👥 Members",    callback_data="menu:members")],
                [InlineKeyboardButton("🗺️ Locations", callback_data="menu:locations"),
                 InlineKeyboardButton("⚔️ Attack",     callback_data="menu:attack")],
                [InlineKeyboardButton("📦 Inventory",  callback_data="menu:inventory"),
                 InlineKeyboardButton("🏆 Leaderboard", callback_data="menu:leaderboard")],
            ]
            text = f"🏠 Main Menu\nWelcome, *{user.get('username','')}*!"
            return await smart_edit(q, text, kb)

        # Inventory list
        if menu == "inventory":
            inv = user.get("inventory", [])
            text = "📦 Your inventory:" + ("\n" + "\n".join(i["name"] for i in inv) if inv else " empty.")
            kb = [
                [InlineKeyboardButton(i["name"], callback_data=f"detail:inventory:{i['name']}")]
                for i in inv
            ]
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
            return await smart_edit(q, text, kb)

        # Shop list
        if menu == "shop":
            kb = [
                [InlineKeyboardButton(n, callback_data=f"detail:shop:{n}")]
                for n in SHOP_ITEMS
            ]
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
            return await smart_edit(q, "🛒 Shop:", kb)

        # Members
        if menu == "members":
            members = user.get("members", [])
            txt = "👥 Team Members:\n" + "\n".join(members) if members else "No members."
            kb = [[InlineKeyboardButton("🔙 Back", callback_data="menu:main")]]
            return await smart_edit(q, txt, kb)

        # Leaderboard
        if menu == "leaderboard":
            rows = repo.scan_leaderboard()
            txt = "🏆 Leaderboard:\n" + "\n".join(f"{r['team']} — {r['points']:.1f}" for r in rows)
            kb = [[InlineKeyboardButton("🔙 Back", callback_data="menu:main")]]
            return await smart_edit(q, txt, kb)

        # Stubs
        if menu in ("locations", "attack"):
            emoji = "🗺️" if menu=="locations" else "⚔️"
            return await smart_edit(q, f"{emoji} {menu.capitalize()}: (coming soon)",
                                    [[InlineKeyboardButton("🔙 Back", callback_data="menu:main")]])

    # ── Detail Views ───────────────────────────────────────────────────────────
    if cmd == "detail":
        source, name = args

        # Inventory item detail
        if source == "inventory":
            inv  = user.get("inventory", [])
            item = next((i for i in inv if i["name"] == name), None)
            if not item:
                return await q.answer("❌ Item not found", show_alert=True)

            text = f"*{name}*\n\n{item.get('description','')}"
            kb = [
                [InlineKeyboardButton("🛠️ Use", callback_data=f"inv_use:{name}")],
                [InlineKeyboardButton("🔙 Back", callback_data="menu:inventory")],
            ]
            return await smart_edit(q, text, kb)

        # Shop item detail
        if source == "shop":
            item = SHOP_ITEMS.get(name)
            if not item:
                return await q.answer("❌ Item not found", show_alert=True)

            text = (
                f"*{name}*\n\n{item['description']}\n"
                f"Cost: {item['cost_gp']} gunpowder, {item['cost_money']} money"
            )
            kb = [
                [InlineKeyboardButton("🛒 Buy", callback_data=f"buy:{name}")],
                [InlineKeyboardButton("🔙 Back", callback_data="menu:shop")],
            ]
            return await smart_edit(q, text, kb)

    # ── Buy / Use Actions ────────────────────────────────────────────────────────
    if cmd == "buy":
        name = args[0]
        itm  = SHOP_ITEMS[name]
        ok   = repo.buy_item(user["user_id"], itm["cost_gp"], itm["cost_money"],
                             {"name": name, "description": itm["description"]})
        return await q.answer("✅ Bought!" if ok else "❌ Not enough resources.", show_alert=True)

    if cmd == "inv_use":
        name = args[0]
        ok   = repo.use_item(user["user_id"], name)
        return await q.answer("✅ Used!" if ok else "❌ Could not use.", show_alert=True)

# ─── APP SETUP & LAMBDA ENTRYPOINT ────────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("init",  init_cmd))
app.add_handler(CallbackQueryHandler(button_handler))

async def async_main(event, context):
    body   = json.loads(event.get("body","{}"))
    update = Update.de_json(body, app.bot)
    async with app:
        await app.process_update(update)
    return {"statusCode":200, "body": json.dumps({"status":"ok"})}

def lambda_handler(event, context):
    return asyncio.run(async_main(event, context))
