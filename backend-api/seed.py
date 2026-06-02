from sqlalchemy.orm import Session
import models

def seed_database(db: Session):
    if db.query(models.Dossier).count() == 0:
        dossiers = [
            models.Dossier(name="Chefe do estágio", classification="Aliado", threat_level="Baixo", role="Supervisor", strengths="Conhecimento do negócio", weaknesses="Micromanagement", notes="Aprovar relatórios com ele primeiro."),
            models.Dossier(name="Colega de equipa folgado", classification="Neutro", threat_level="Médio", role="Developer", strengths="Sabe os atalhos todos", weaknesses="Procrastinação", notes="Não depender dele para prazos apertados."),
            models.Dossier(name="Mentor de código", classification="Aliado", threat_level="Nulo", role="Senior Developer", strengths="Python, Arquitetura", weaknesses="Tempo limitado", notes="Sempre disponível para code reviews se marcados com antecedência."),
            models.Dossier(name="Cliente Difícil", classification="Hostil", threat_level="Alto", role="Stakeholder", strengths="Orçamento", weaknesses="Muda de ideias constantemente", notes="Documentar tudo o que ele diz.")
        ]
        db.add_all(dossiers)
    
    if db.query(models.Note).count() == 0:
        notes = [
            models.Note(content="Lembrar de fazer git push antes de sair."),
            models.Note(content="O bug na página de login só acontece em Safari."),
            models.Note(content="Reunião de sync às 10:00 amanhã."),
            models.Note(content="Comprar café a caminho do escritório."),
            models.Note(content="Verificar os logs do docker-compose se a base de dados falhar.")
        ]
        db.add_all(notes)
        
    if db.query(models.Shortcut).count() == 0:
        shortcuts = [
            models.Shortcut(name="Limpar Docker", command_or_path="docker system prune -a --volumes -f", description="Limpa todos os containers, imagens e volumes não usados."),
            models.Shortcut(name="Logs da API", command_or_path="docker logs -f vexylo_api", description="Acompanha os logs da API em tempo real."),
            models.Shortcut(name="Restart DB", command_or_path="docker restart vexylo_db", description="Reinicia o serviço da base de dados PostgreSQL.")
        ]
        db.add_all(shortcuts)
        
    db.commit()
