traffic-spike =
    ⚠️ <b>Traffic spike detected</b>

    <b>User:</b> { $tg_id }
    <b>Subscription:</b> { $username }
    <b>Increase:</b> { $traffic_diff_gb } GB / { $interval_minutes } min
    { $nodes_info }<b>Alerts for this user:</b> { $alert_count }
    <b>Time:</b> { $time }

total-limit =
    🚨 <b>Traffic limit exceeded</b>

    <b>User:</b> { $tg_id }
    <b>Subscription:</b> { $username }
    <b>Consumed:</b> { $traffic_gb } GB / { $hours } h
    { $nodes_info }<b>Alerts for this user:</b> { $alert_count }
    <b>Time:</b> { $time }

nodes-info-header = <b>By server:</b>

node-line = { $flag } { $name }: { $traffic_gb } GB

hourly-stats =
    📊 <b>Hourly traffic report</b>

    <b>Total users:</b> { $total_users }
    <b>Active users:</b> { $active_users }
    <b>Total traffic:</b> { $total_traffic_gb } GB
    <b>Top user:</b> { $top_user_username } — { $top_user_traffic_gb } GB
    <b>Alerts sent:</b> { $alerts_count }
    <b>Period:</b> { $time }

service-started =
    🛡 <b>TrafficGuard started</b>

    <b>Spike threshold:</b> { $interval_threshold } GB / { $interval } min
    <b>Total threshold:</b> { $total_threshold } GB / { $total_hours } h
