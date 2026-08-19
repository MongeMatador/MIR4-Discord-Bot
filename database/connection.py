import asyncpg
import os
import socket
from urllib.parse import urlparse
from config import Config, logger

class DatabaseManager:
    _pool = None

    @classmethod
    async def initialize(cls):
        logger.info("Inicializando Pool de conexões com o Supabase PostgreSQL...")
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("CRÍTICO: A variável DATABASE_URL não foi configurada no Render!")

        # Parseia a URL de conexão
        parsed = urlparse(db_url)
        hostname = parsed.hostname
        port = parsed.port or 5432
        username = parsed.username
        password = parsed.password
        database = parsed.path.lstrip("/")

        # RESOLVEDOR INTELIGENTE DE DNS (Força IPv4 para evitar "Network is unreachable" no Render)
        try:
            logger.info(f"Resolvendo DNS de {hostname} para IPv4...")
            addr_infos = socket.getaddrinfo(hostname, port, family=socket.AF_INET, proto=socket.IPPROTO_TCP)
            ipv4_ip = addr_infos[0][4][0]
            logger.info(f"Sucesso! Host {hostname} resolvido para o IP IPv4: {ipv4_ip}")
        except socket.gaierror as dns_err:
            if "db.oauvpoyehhqjqbsuwvzg.supabase.co" in hostname:
                raise ValueError(
                    "\n\n❌ [ERRO CRÍTICO DE REDE]\n"
                    "O endereço 'db.oauvpoyehhqjqbsuwvzg.supabase.co' é estritamente IPv6-only!\n"
                    "Como o Render gratuito não suporta conexões IPv6, o bot não consegue se conectar.\n"
                    "Por favor, altere sua DATABASE_URL no painel do Render para usar a porta 6543 (Connection Pooler):\n"
                    "postgresql://postgres.oauvpoyehhqjqbsuwvzg:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres\n"
                ) from dns_err
            
            logger.warning(f"Não foi possível forçar IPv4 para {hostname}. Usando host original: {dns_err}")
            ipv4_ip = hostname

        # Configura o Pool de conexões com o banco externo de forma segura com SSL
        cls._pool = await asyncpg.create_pool(
            host=ipv4_ip,
            port=port,
            user=username,
            password=password,
            database=database,
            server_hostname=hostname, # Garante que a validação de certificado SSL funcione mesmo conectando via IP direto!
            min_size=1,
            max_size=5,
            command_timeout=60.0
        )

        # Garante a criação estrutural de todas as tabelas
        async with cls._pool.acquire() as conn:
            logger.info("Verificando/Criando tabelas no Supabase...")
            
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
                status TEXT NOT NULL,
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

            logger.info("Estrutura do banco de dados Supabase validada com sucesso!")

    @classmethod
    async def get_connection(cls):
        if not cls._pool:
            await cls.initialize()
        return cls._pool.acquire()
