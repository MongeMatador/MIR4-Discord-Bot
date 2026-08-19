import asyncpg
import os
from config import Config, logger

class DatabaseManager:
    _pool = None

    @classmethod
    async def initialize(cls):
        logger.info("Inicializando Pool de conexões com o Supabase PostgreSQL...")
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("CRÍTICO: A variável DATABASE_URL não foi configurada no Render!")

        # Configura o Pool de conexões com o banco externo
        cls._pool = await asyncpg.create_pool(
            db_url,
            min_size=1,
            max_size=5,
            command_timeout=60.0
        )

        # Garante a criação estrutural de todas as tabelas com BIGINT para IDs do Discord
        async with cls._pool.acquire() as conn:
            logger.info("Verificando esquemas e tabelas no Supabase...")
            
            # Tabela de Configurações de Painéis Principais (Claims de cliques)
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS panel_settings (
                guild_id BIGINT NOT NULL,
                map_type TEXT NOT NULL,
                channel_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, map_type)
            );
            """)

            # Tabela de Canais de Status de Andares (Os placares públicos)
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS floor_dashboards (
                guild_id BIGINT NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                channel_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, map_type, floor)
            );
            """)

            # Tabela de Claims ativas
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                spot_type TEXT NOT NULL,
                room_number INTEGER NOT NULL,
                status TEXT NOT NULL, -- 'ACTIVE', 'VACANT_REMAINING', 'EXPIRED'
                user_id BIGINT NOT NULL,
                username TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ends_at TIMESTAMP NOT NULL,
                tickets INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Tabela de Fila de Espera
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS spot_queues (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                spot_type TEXT NOT NULL,
                user_id BIGINT NOT NULL,
                username TEXT NOT NULL,
                tickets INTEGER NOT NULL,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Tabela de Eventos de Respawn (L1, L2, etc.)
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS floor_events (
                guild_id BIGINT NOT NULL,
                map_type TEXT NOT NULL,
                floor TEXT NOT NULL,
                event_name TEXT NOT NULL,
                last_triggered_at TIMESTAMP,
                last_triggered_by BIGINT,
                PRIMARY KEY (guild_id, map_type, floor, event_name)
            );
            """)

            # Tabela de Canais de Logs de Auditoria da Staff
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_log_channels (
                guild_id BIGINT NOT NULL,
                category TEXT NOT NULL,
                channel_id BIGINT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, category)
            );
            """)

            logger.info("Esquemas de banco PostgreSQL verificados com sucesso no Supabase!")

    @classmethod
    async def get_connection(cls):
        if not cls._pool:
            await cls.initialize()
        return cls._pool.acquire()
