pip install psycopg2-binary

login returns a response of 
refresh and access tokens 

to logout, the auth header needs to have the access token and the refresh token in the request data...
to refresh access tokens send the refresh token in the request body to 
/auth/refresh_token/

this should return a new access and refresh tokens

password change required a logged in user , request data should be "old_password" and "new_password"

python manage.py run_startup_commands initial_items_cat_updated setup_pricing_defaults initial_services initial_vehicle_categories setup_groups