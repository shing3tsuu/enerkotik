from dataclasses import dataclass
from environs import Env

@dataclass
class TgBot:
    token: str
    admin_ids: list[int]

@dataclass
class DBConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

@dataclass
class Config:
    tg_bot: TgBot
    db: DBConfig

def load_config(path: str | None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
    tg_bot=TgBot(
        token=env('BOT_TOKEN'),
        admin_ids=list(map(int, env.list('ADMIN_IDS')))
    ),
    db=DBConfig(
        host=env('DB_HOST'),
        port=env('DB_PORT'),
        name=env('DB_NAME'),
        user=env('DB_USER'),
        password=env('DB_PASSWORD')
    )
)
