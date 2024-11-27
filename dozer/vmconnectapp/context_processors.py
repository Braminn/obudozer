''' context_processors.py '''
from datetime import datetime
from vmconnectapp.models import SystemInfo

def add_last_update_time(request):
    """
    Контекстный процессор для добавления времени обновления в шаблоны.
    """
    last_update = SystemInfo.objects.filter(name="last_update_time").first()
    if last_update and last_update.value:
        # Преобразуем строку в объект datetime и форматируем
        update_time = datetime.fromisoformat(last_update.value)
        readable_time = update_time.strftime("%d.%m.%Y, %H:%M")
    else:
        readable_time = "Время обновления отсутствует"

    return {
        'last_update_time': readable_time,
    }
