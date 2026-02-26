traffic-spike =
    ⚠️ <b>Прирост трафика обнаружен</b>

    <b>Пользователь:</b> { $tg_id }
    <b>Подписка:</b> { $username }
    <b>Прирост:</b> { $traffic_diff_gb } ГБ / { $interval_minutes } мин
    { $nodes_info }<b>Алертов по пользователю:</b> { $alert_count }
    <b>Время:</b> { $time }

total-limit =
    🚨 <b>Превышен лимит трафика</b>

    <b>Пользователь:</b> { $tg_id }
    <b>Подписка:</b> { $username }
    <b>Потреблено:</b> { $traffic_gb } ГБ / { $hours } ч
    { $nodes_info }<b>Алертов по пользователю:</b> { $alert_count }
    <b>Время:</b> { $time }

nodes-info-header = <b>По серверам:</b>

node-line = { $flag } { $name }: { $traffic_gb } ГБ

hourly-stats =
    📊 <b>Почасовой отчёт по трафику</b>

    <b>Всего пользователей:</b> { $total_users }
    <b>Активных:</b> { $active_users }
    <b>Общий трафик:</b> { $total_traffic_gb } ГБ
    <b>Топ пользователь:</b> { $top_user_username } — { $top_user_traffic_gb } ГБ
    <b>Алертов:</b> { $alerts_count }
    <b>Период:</b> { $time }

service-started =
    🛡 <b>TrafficGuard запущен</b>

    <b>Порог прироста:</b> { $interval_threshold } ГБ / { $interval } мин
    <b>Порог общий:</b> { $total_threshold } ГБ / { $total_hours } ч
