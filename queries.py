"""SQL insight queries (mirrors sql/insights.sql). Kept as a Python module so the
app works even if the sql/ folder is not deployed."""

QUERIES = {'usage_by_weekday': {'question': 'Which days of the week are users most active on?',
                      'sql': 'SELECT\n'
                             '    Weekday,\n'
                             '    ROUND(AVG(TotalSteps), 0)      AS avg_steps,\n'
                             '    ROUND(AVG(Calories), 0)        AS avg_calories,\n'
                             '    ROUND(AVG(VeryActiveMinutes), 1) AS avg_very_active_min,\n'
                             '    ROUND(AVG(SedentaryMinutes), 1)  AS avg_sedentary_min\n'
                             'FROM daily_activity\n'
                             'GROUP BY Weekday\n'
                             'ORDER BY\n'
                             '    CASE Weekday\n'
                             "        WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' "
                             'THEN 3\n'
                             "        WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' "
                             'THEN 6\n'
                             "        WHEN 'Sunday' THEN 7 END;"},
 'steps_calories_correlation': {'question': 'Is there a relationship between daily steps and '
                                            'calories burned?',
                                'sql': 'SELECT\n'
                                       '    TotalSteps,\n'
                                       '    Calories,\n'
                                       '    VeryActiveMinutes,\n'
                                       '    SedentaryMinutes\n'
                                       'FROM daily_activity\n'
                                       'WHERE TotalSteps > 0;'},
 'activity_intensity_breakdown': {'question': 'How do users split their time across activity '
                                              'intensities?',
                                  'sql': 'SELECT\n'
                                         '    ROUND(AVG(VeryActiveMinutes), 1)   AS '
                                         'avg_very_active,\n'
                                         '    ROUND(AVG(MediumActiveMinutes), 1) AS '
                                         'avg_moderately_active,\n'
                                         '    ROUND(AVG(SedentaryMinutes), 1)    AS avg_sedentary\n'
                                         'FROM daily_activity;'},
 'sedentary_vs_sleep': {'question': 'Do more sedentary minutes relate to less/worse sleep?',
                        'sql': 'SELECT\n'
                               '    a.Id,\n'
                               '    a.ActivityDate,\n'
                               '    a.SedentaryMinutes,\n'
                               '    s.TotalMinutesAsleep,\n'
                               '    s.TotalTimeInBed,\n'
                               '    (s.TotalTimeInBed - s.TotalMinutesAsleep) AS '
                               'minutes_awake_in_bed\n'
                               'FROM daily_activity a\n'
                               'JOIN sleep_day s\n'
                               '    ON a.Id = s.Id AND DATE(a.ActivityDate) = DATE(s.SleepDay)\n'
                               'WHERE s.TotalMinutesAsleep IS NOT NULL;'},
 'avg_sleep_by_user': {'question': 'Which users are getting enough sleep (>= 7h recommended)?',
                       'sql': 'SELECT\n'
                              '    Id,\n'
                              '    COUNT(*)                                   AS nights_logged,\n'
                              '    ROUND(AVG(TotalMinutesAsleep) / 60.0, 2)    AS '
                              'avg_hours_asleep,\n'
                              '    ROUND(AVG(TotalTimeInBed) / 60.0, 2)        AS '
                              'avg_hours_in_bed,\n'
                              "    CASE WHEN AVG(TotalMinutesAsleep) / 60.0 >= 7 THEN 'Meets "
                              "recommendation'\n"
                              "         ELSE 'Below recommendation' END        AS sleep_status\n"
                              'FROM sleep_day\n'
                              'GROUP BY Id\n'
                              'ORDER BY avg_hours_asleep;'},
 'hourly_activity_pattern': {'question': 'What time of day are users most active / burning most '
                                         'calories?',
                             'sql': 'SELECT\n'
                                    "    strftime('%H', ActivityHour) AS hour_of_day,\n"
                                    '    ROUND(AVG(Calories), 1)      AS avg_calories\n'
                                    'FROM hourly_calories\n'
                                    'GROUP BY hour_of_day\n'
                                    'ORDER BY hour_of_day;'},
 'hourly_intensity_pattern': {'question': 'What time of day has the highest exercise intensity?',
                              'sql': 'SELECT\n'
                                     "    strftime('%H', ActivityHour) AS hour_of_day,\n"
                                     '    ROUND(AVG(TotalIntensity), 2) AS avg_intensity\n'
                                     'FROM hourly_intensities\n'
                                     'GROUP BY hour_of_day\n'
                                     'ORDER BY hour_of_day;'},
 'user_activity_segments': {'question': 'How can we segment users by activity level? (for '
                                        'Bellabeat marketing personas)',
                            'sql': 'SELECT\n'
                                   '    Id,\n'
                                   '    ROUND(AVG(TotalSteps), 0) AS avg_steps,\n'
                                   '    CASE\n'
                                   "        WHEN AVG(TotalSteps) < 5000 THEN 'Sedentary'\n"
                                   "        WHEN AVG(TotalSteps) < 7500 THEN 'Low Active'\n"
                                   "        WHEN AVG(TotalSteps) < 10000 THEN 'Somewhat Active'\n"
                                   "        ELSE 'Active'\n"
                                   '    END AS activity_segment\n'
                                   'FROM daily_activity\n'
                                   'GROUP BY Id\n'
                                   'ORDER BY avg_steps DESC;'},
 'segment_summary': {'question': 'How many users fall into each activity segment, and how do they '
                                 'compare?',
                     'sql': 'WITH per_user AS (\n'
                            '    SELECT\n'
                            '        Id,\n'
                            '        AVG(TotalSteps) AS avg_steps,\n'
                            '        AVG(Calories) AS avg_calories,\n'
                            '        AVG(SedentaryMinutes) AS avg_sedentary\n'
                            '    FROM daily_activity\n'
                            '    GROUP BY Id\n'
                            '),\n'
                            'segmented AS (\n'
                            '    SELECT *,\n'
                            '        CASE\n'
                            "            WHEN avg_steps < 5000 THEN 'Sedentary'\n"
                            "            WHEN avg_steps < 7500 THEN 'Low Active'\n"
                            "            WHEN avg_steps < 10000 THEN 'Somewhat Active'\n"
                            "            ELSE 'Active'\n"
                            '        END AS activity_segment\n'
                            '    FROM per_user\n'
                            ')\n'
                            'SELECT\n'
                            '    activity_segment,\n'
                            '    COUNT(*) AS num_users,\n'
                            '    ROUND(AVG(avg_steps), 0) AS avg_steps,\n'
                            '    ROUND(AVG(avg_calories), 0) AS avg_calories,\n'
                            '    ROUND(AVG(avg_sedentary), 0) AS avg_sedentary_minutes\n'
                            'FROM segmented\n'
                            'GROUP BY activity_segment\n'
                            'ORDER BY avg_steps;'},
 'device_usage_frequency': {'question': 'How consistently do users log/wear their device? '
                                        '(engagement proxy)',
                            'sql': 'SELECT\n'
                                   '    Id,\n'
                                   '    COUNT(DISTINCT ActivityDate) AS days_logged,\n'
                                   '    ROUND(100.0 * COUNT(DISTINCT ActivityDate) / (\n'
                                   '        SELECT COUNT(DISTINCT ActivityDate) FROM '
                                   'daily_activity\n'
                                   '    ), 1) AS pct_of_period_logged\n'
                                   'FROM daily_activity\n'
                                   'GROUP BY Id\n'
                                   'ORDER BY days_logged DESC;'},
 'weight_trend': {'question': 'How does logged weight/BMI change over time for users who track it?',
                  'sql': 'SELECT\n'
                         '    Id,\n'
                         '    Date,\n'
                         '    WeightKg,\n'
                         '    BMI\n'
                         'FROM weight_log\n'
                         'ORDER BY Id, Date;'},
 'heartrate_daily_summary': {'question': 'What do resting/average heart-rate patterns look like '
                                         'per user per day?',
                             'sql': 'SELECT\n'
                                    '    Id,\n'
                                    '    DATE(Time) AS day,\n'
                                    '    ROUND(AVG(AvgHeartRate), 1) AS avg_hr,\n'
                                    '    ROUND(MIN(AvgHeartRate), 1) AS min_hr,\n'
                                    '    ROUND(MAX(AvgHeartRate), 1) AS max_hr\n'
                                    'FROM heartrate_minute\n'
                                    'GROUP BY Id, day\n'
                                    'ORDER BY Id, day;'},
 'total_summary_kpis': {'question': 'Top-line KPIs for the dashboard header',
                        'sql': 'SELECT\n'
                               '    (SELECT COUNT(DISTINCT Id) FROM daily_activity)            AS '
                               'total_users,\n'
                               '    (SELECT ROUND(AVG(TotalSteps), 0) FROM daily_activity)     AS '
                               'avg_daily_steps,\n'
                               '    (SELECT ROUND(AVG(Calories), 0) FROM daily_activity)       AS '
                               'avg_daily_calories,\n'
                               '    (SELECT ROUND(AVG(TotalMinutesAsleep) / 60.0, 2) FROM '
                               'sleep_day) AS avg_sleep_hours,\n'
                               '    (SELECT ROUND(AVG(SedentaryMinutes) / 60.0, 2) FROM '
                               'daily_activity) AS avg_sedentary_hours;'}}
