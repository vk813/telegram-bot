import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from telegram.ext import CommandHandler

from bot import filter_add_conv, service_conv
from handlers.my_calendar import reg_conv
from handlers.filter_photo import add_filter_photo_conv
from handlers.profile import phone_conv
from handlers.know_filter import know_filter_conv
from handlers.payments import payments_conv
from handlers.crm_handlers import crm_conv_handler


def _has_start_handler(conv):
    return any(isinstance(h, CommandHandler) and "start" in h.commands for h in conv.fallbacks)


def test_no_start_in_conversation_fallbacks():
    conversations = [
        reg_conv,
        filter_add_conv,
        service_conv,
        add_filter_photo_conv,
        phone_conv,
        know_filter_conv,
        payments_conv,
        crm_conv_handler,
    ]
    assert all(not _has_start_handler(c) for c in conversations)
