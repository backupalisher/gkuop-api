"""
Вспомогательные функции
"""
import sys
from typing import Dict
from datetime import datetime, timedelta

def format_ticket_info(ticket: Dict) -> str:
    """Форматирование информации о заявке для вывода"""
    lines = [
        f"Заявка #{ticket.get('ticket_number', 'N/A')}",
        f"Статус: {ticket.get('status', 'N/A')}",
        f"Приоритет: {ticket.get('priority', 'N/A')}",
        f"Устройство: {ticket.get('printer_model', 'N/A')}",
        f"Инв. номер: {ticket.get('inventory_number', 'N/A')}",
        f"Офис: {ticket.get('office', 'N/A')}",
        f"Кабинет: {ticket.get('cabinet', 'N/A')}",
        f"Дата создания: {ticket.get('first_received_date', 'N/A')}",
    ]
    return "\n".join(lines)

def print_statistics(stats: Dict):
    """Вывод статистики"""
    print("\n" + "="*50)
    print("СТАТИСТИКА ЗАЯВОК")
    print("="*50)
    print(f"Всего заявок: {stats.get('total', 0)}")
    print(f"Активных заявок: {stats.get('active', 0)}")
    print(f"В работе: {stats.get('in_progress', 0)}")
    print(f"Согласовано: {stats.get('approved', 0)}")
    print(f"Уникальных устройств: {stats.get('unique_devices', 0)}")
    print("="*50 + "\n")

def parse_date_range(days: int = 7) -> datetime:
    """Получение даты начала периода"""
    return datetime.now() - timedelta(days=days)

def confirm_action(message: str) -> bool:
    """Подтверждение действия пользователя"""
    response = input(f"{message} (y/n): ").lower()
    return response in ['y', 'yes', 'да']

def exit_with_error(message: str):
    """Выход с ошибкой"""
    print(f"\n✗ ОШИБКА: {message}")
    sys.exit(1)