SELECT
    DATE(created_at) AS signup_date,
    COUNT(*) AS users_created
FROM public.users
GROUP BY DATE(created_at)
ORDER BY signup_date DESC;
