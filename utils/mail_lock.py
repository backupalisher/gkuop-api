"""Общий замок IMAP: автозагрузка писем и ручная перестройка не идут одновременно."""
import threading

mail_lock = threading.Lock()
