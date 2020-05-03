First install Python packages

```
cd src
pip install -r requirements.txt
```

Then you can run it as

```
export sp_env=local
Python app.py
```

sp_env = local|proxy_prod

local uses in memory cache;
proxy_prod uses production cache but proxied through, since you can't access production cache directly.
