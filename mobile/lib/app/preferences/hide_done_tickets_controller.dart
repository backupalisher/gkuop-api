import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _hideDoneTicketsKey = 'hide_done_tickets';

/// Скрывать выполненные / решённые / закрытые заявки на вкладке «Активные».
/// Хранится локально на устройстве (SharedPreferences).
class HideDoneTicketsController extends StateNotifier<bool> {
  HideDoneTicketsController() : super(false) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool(_hideDoneTicketsKey) ?? false;
  }

  Future<void> setHidden(bool value) async {
    state = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_hideDoneTicketsKey, value);
  }

  Future<void> toggle() => setHidden(!state);
}

final hideDoneTicketsProvider =
    StateNotifierProvider<HideDoneTicketsController, bool>((ref) {
      return HideDoneTicketsController();
    });

bool isDoneTicketStatus(String? status) {
  final s = (status ?? '').toLowerCase();
  return s.contains('выполн') ||
      s.contains('решён') ||
      s.contains('решен') ||
      s.contains('закрыт');
}
