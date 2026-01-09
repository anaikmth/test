from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    money = db.Column(db.Integer, default=5000, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    clicker_data = db.relationship('ClickerData', backref='user', uselist=False, cascade='all, delete-orphan')
    game_history = db.relationship('GameHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', secondary='user_achievements', backref='users')
    
    def set_password(self, password):
        """Hash le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def add_money(self, amount):
        """Ajoute de l'argent (avec validation)"""
        if amount < 0:
            raise ValueError("Le montant ne peut pas être négatif")
        self.money += amount
        db.session.commit()
    
    def remove_money(self, amount):
        """Retire de l'argent (avec validation)"""
        if amount < 0:
            raise ValueError("Le montant ne peut pas être négatif")
        if self.money < amount:
            raise ValueError("Fonds insuffisants")
        self.money -= amount
        db.session.commit()
    
    def get_stats(self):
        """Retourne les statistiques du joueur"""
        games = self.game_history.all()
        
        total_games = len(games)
        total_wins = sum(1 for g in games if g.result == 'win')
        total_losses = sum(1 for g in games if g.result == 'lose')
        total_wagered = sum(g.bet_amount for g in games)
        total_winnings = sum(g.profit for g in games if g.profit > 0)
        
        return {
            'total_games': total_games,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'win_rate': round((total_wins / total_games * 100), 1) if total_games > 0 else 0,
            'total_wagered': total_wagered,
            'total_winnings': total_winnings,
            'net_profit': total_winnings - total_wagered
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class ClickerData(db.Model):
    """Données du Money Clicker par utilisateur"""
    __tablename__ = 'clicker_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    click_power = db.Column(db.Integer, default=1)
    click_level = db.Column(db.Integer, default=1)
    auto_level = db.Column(db.Integer, default=0)
    factory_level = db.Column(db.Integer, default=0)
    bank_level = db.Column(db.Integer, default=0)
    
    click_cost = db.Column(db.Integer, default=10)
    auto_cost = db.Column(db.Integer, default=50)
    factory_cost = db.Column(db.Integer, default=200)
    bank_cost = db.Column(db.Integer, default=1000)
    
    total_clicks = db.Column(db.Integer, default=0)
    total_earned = db.Column(db.Integer, default=0)
    
    @property
    def passive_income(self):
        """Calcule le revenu passif"""
        return self.auto_level + (self.factory_level * 5) + (self.bank_level * 20)
    
    def __repr__(self):
        return f'<ClickerData user_id={self.user_id}>'


class GameHistory(db.Model):
    """Historique des parties"""
    __tablename__ = 'game_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    game_type = db.Column(db.String(20), nullable=False, index=True)  # blackjack, roulette, minebomb, slots
    
    bet_amount = db.Column(db.Integer, nullable=False)
    result = db.Column(db.String(10), nullable=False)  # win, lose, draw
    profit = db.Column(db.Integer, default=0)  # Peut être négatif
    multiplier = db.Column(db.Float, default=1.0)
    
    details = db.Column(db.JSON)  # Détails spécifiques au jeu (cartes, numéro roulette, etc.)
    played_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<GameHistory {self.game_type} - {self.result}>'


class Achievement(db.Model):
    """Succès débloquables"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(10), default='🏆')
    reward = db.Column(db.Integer, default=0)  # Bonus en argent
    
    # Conditions
    condition_type = db.Column(db.String(50))  # total_wins, jackpot, win_streak, etc.
    condition_value = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Achievement {self.name}>'


# Table association pour les succès des utilisateurs
user_achievements = db.Table('user_achievements',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievements.id'), primary_key=True),
    db.Column('unlocked_at', db.DateTime, default=datetime.utcnow)
)


class GlobalStats(db.Model):
    """Statistiques globales (tous joueurs confondus)"""
    __tablename__ = 'global_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    stat_key = db.Column(db.String(50), unique=True, nullable=False)
    stat_value = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def increment(key, value=1):
        """Incrémente une stat globale"""
        stat = GlobalStats.query.filter_by(stat_key=key).first()
        if not stat:
            stat = GlobalStats(stat_key=key, stat_value=value)
            db.session.add(stat)
        else:
            stat.stat_value += value
        db.session.commit()
    
    @staticmethod
    def get_value(key, default=0):
        """Récupère une stat globale"""
        stat = GlobalStats.query.filter_by(stat_key=key).first()
        return stat.stat_value if stat else default
    
    def __repr__(self):
        return f'<GlobalStats {self.stat_key}={self.stat_value}>'


class DailyBonus(db.Model):
    """Bonus quotidiens"""
    __tablename__ = 'daily_bonuses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    claimed_date = db.Column(db.Date, nullable=False)
    bonus_amount = db.Column(db.Integer, nullable=False)
    streak_days = db.Column(db.Integer, default=1)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'claimed_date', name='unique_daily_bonus'),
    )
    
    def __repr__(self):
        return f'<DailyBonus user_id={self.user_id} date={self.claimed_date}>'