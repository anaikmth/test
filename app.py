from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
import random
import os
import json

# Créer l'app Flask AVANT d'importer les modèles
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casinoeuil.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-very-secret-2024')app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Importer db et les modèles APRÈS avoir configuré l'app
from models import db, User, ClickerData, GameHistory, Achievement, GlobalStats, DailyBonus

# Initialisation
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================
# ROUTES D'AUTHENTIFICATION
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Le nom d\'utilisateur doit avoir au moins 3 caractères'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Le mot de passe doit avoir au moins 6 caractères'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Nom d\'utilisateur déjà pris'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email déjà utilisé'}), 400
        
        user = User(username=username, email=email, money=5000)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        clicker_data = ClickerData(user_id=user.id)
        db.session.add(clicker_data)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Compte créé avec succès!'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True})
        
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    return redirect(url_for('login'))

# ============================================
# ROUTES PRINCIPALES
# ============================================

@app.route('/')
@login_required
def index():
    """Page principale"""
    return render_template('index.html', money=current_user.money)

@app.route('/profile')
@login_required
def profile():
    """Page de profil utilisateur"""
    return render_template('profile.html')

@app.route('/api/get_stats')
@login_required
def get_stats():
    """Récupère les statistiques globales"""
    stats = get_global_stats()
    return jsonify(stats)

@app.route('/api/user_stats')
@login_required
def user_stats():
    """Statistiques personnelles du joueur"""
    return jsonify(current_user.get_stats())

def get_global_stats():
    """Calcule les stats globales depuis la DB"""
    all_games = GameHistory.query.all()
    
    total_games = len(all_games)
    total_wins = sum(1 for g in all_games if g.result == 'win')
    total_losses = sum(1 for g in all_games if g.result == 'lose')
    total_wagered = sum(g.bet_amount for g in all_games)
    total_winnings = sum(g.profit for g in all_games if g.profit > 0)
    
    biggest_win_game = GameHistory.query.filter(GameHistory.profit > 0).order_by(GameHistory.profit.desc()).first()
    biggest_loss_game = GameHistory.query.filter(GameHistory.profit < 0).order_by(GameHistory.profit.asc()).first()
    
    def get_game_stats(game_type):
        games = GameHistory.query.filter_by(game_type=game_type).all()
        wins = sum(1 for g in games if g.result == 'win')
        wagered = sum(g.bet_amount for g in games)
        won = sum(g.profit for g in games if g.profit > 0)
        return {
            'games': len(games),
            'wins': wins,
            'wagered': wagered,
            'won': won
        }
    
    return {
        'totalGames': total_games,
        'totalWins': total_wins,
        'totalLosses': total_losses,
        'biggestWin': biggest_win_game.profit if biggest_win_game else 0,
        'biggestLoss': abs(biggest_loss_game.profit) if biggest_loss_game else 0,
        'totalWagered': total_wagered,
        'totalWinnings': total_winnings,
        'blackjack': get_game_stats('blackjack'),
        'roulette': get_game_stats('roulette'),
        'minebomb': get_game_stats('minebomb'),
        'slots': get_game_stats('slots')
    }

# ============================================
# MONEY CLICKER
# ============================================

@app.route('/api/clicker/get_data')
@login_required
def clicker_get_data():
    """Récupère les données du clicker"""
    clicker = current_user.clicker_data
    
    if not clicker:
        clicker = ClickerData(user_id=current_user.id)
        db.session.add(clicker)
        db.session.commit()
    
    return jsonify({
        'clickPower': clicker.click_power,
        'clickLevel': clicker.click_level,
        'autoLevel': clicker.auto_level,
        'factoryLevel': clicker.factory_level,
        'bankLevel': clicker.bank_level,
        'clickCost': clicker.click_cost,
        'autoCost': clicker.auto_cost,
        'factoryCost': clicker.factory_cost,
        'bankCost': clicker.bank_cost,
        'passiveIncome': clicker.passive_income
    })

@app.route('/api/clicker/click', methods=['POST'])
@login_required
def clicker_click():
    """Gère le clic"""
    clicker = current_user.clicker_data
    current_user.add_money(clicker.click_power)
    
    clicker.total_clicks += 1
    clicker.total_earned += clicker.click_power
    db.session.commit()
    
    return jsonify({'money': current_user.money})

@app.route('/api/clicker/upgrade', methods=['POST'])
@login_required
def clicker_upgrade():
    """Achète une amélioration"""
    data = request.json
    upgrade_type = data.get('type')
    
    clicker = current_user.clicker_data
    
    if upgrade_type == 'click':
        cost = clicker.click_cost
        if current_user.money >= cost:
            current_user.remove_money(cost)
            clicker.click_power += 1
            clicker.click_level += 1
            clicker.click_cost = int(cost * 1.5)
        else:
            return jsonify({'error': 'Pas assez d\'argent'}), 400
    
    elif upgrade_type == 'auto':
        cost = clicker.auto_cost
        if current_user.money >= cost:
            current_user.remove_money(cost)
            clicker.auto_level += 1
            clicker.auto_cost = int(cost * 1.8)
        else:
            return jsonify({'error': 'Pas assez d\'argent'}), 400
    
    elif upgrade_type == 'factory':
        cost = clicker.factory_cost
        if current_user.money >= cost:
            current_user.remove_money(cost)
            clicker.factory_level += 1
            clicker.factory_cost = int(cost * 2)
        else:
            return jsonify({'error': 'Pas assez d\'argent'}), 400
    
    elif upgrade_type == 'bank':
        cost = clicker.bank_cost
        if current_user.money >= cost:
            current_user.remove_money(cost)
            clicker.bank_level += 1
            clicker.bank_cost = int(cost * 2.5)
        else:
            return jsonify({'error': 'Pas assez d\'argent'}), 400
    
    db.session.commit()
    
    return jsonify({
        'money': current_user.money,
        'clickPower': clicker.click_power,
        'clickLevel': clicker.click_level,
        'autoLevel': clicker.auto_level,
        'factoryLevel': clicker.factory_level,
        'bankLevel': clicker.bank_level,
        'clickCost': clicker.click_cost,
        'autoCost': clicker.auto_cost,
        'factoryCost': clicker.factory_cost,
        'bankCost': clicker.bank_cost,
        'passiveIncome': clicker.passive_income
    })

@app.route('/api/clicker/passive', methods=['POST'])
@login_required
def clicker_passive():
    """Revenu passif"""
    clicker = current_user.clicker_data
    passive = clicker.passive_income
    
    if passive > 0:
        current_user.add_money(passive)
        clicker.total_earned += passive
        db.session.commit()
    
    return jsonify({'money': current_user.money})

# ============================================
# BLACKJACK
# ============================================

def create_deck():
    """Crée un jeu de 52 cartes"""
    suits = ['♥', '♦', '♣', '♠']
    values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    return [{'suit': suit, 'value': value} for suit in suits for value in values]

def card_value(card):
    """Retourne la valeur d'une carte"""
    if card['value'] in ['J', 'Q', 'K']:
        return 10
    elif card['value'] == 'A':
        return 11
    else:
        return int(card['value'])

def hand_total(hand):
    """Calcule le total d'une main"""
    total = sum(card_value(card) for card in hand)
    aces = sum(1 for card in hand if card['value'] == 'A')
    
    while total > 21 and aces:
        total -= 10
        aces -= 1
    
    return total

@app.route('/api/blackjack/start', methods=['POST'])
@login_required
def blackjack_start():
    """Démarre une partie de blackjack"""
    data = request.json
    bet = int(data.get('bet', 50))
    
    if bet < 10:
        return jsonify({'error': 'Mise minimum : 10$'}), 400
    
    if bet > current_user.money:
        return jsonify({'error': 'Mise trop élevée'}), 400
    
    current_user.remove_money(bet)
    
    # Créer le deck (entre 1 et 8 decks)
    num_decks = random.randint(1, 8)
    deck = create_deck() * num_decks
    random.shuffle(deck)
    
    # Distribuer les cartes
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    # Sauvegarder dans la session
    session['blackjack'] = {
        'bet': bet,
        'deck': deck,
        'player_hand': player_hand,
        'dealer_hand': dealer_hand,
        'num_decks': num_decks
    }
    
    return jsonify({
        'money': current_user.money,
        'player_hand': player_hand,
        'dealer_hand': dealer_hand,
        'player_total': hand_total(player_hand),
        'num_decks': num_decks
    })

@app.route('/api/blackjack/hit', methods=['POST'])
@login_required
def blackjack_hit():
    """Tirer une carte"""
    game = session.get('blackjack')
    if not game:
        return jsonify({'error': 'Pas de partie en cours'}), 400
    
    card = game['deck'].pop()
    game['player_hand'].append(card)
    session['blackjack'] = game
    
    player_total = hand_total(game['player_hand'])
    busted = player_total > 21
    
    return jsonify({
        'player_hand': game['player_hand'],
        'player_total': player_total,
        'busted': busted
    })

@app.route('/api/blackjack/stand', methods=['POST'])
@login_required
def blackjack_stand():
    """Se coucher et terminer la partie"""
    game = session.get('blackjack')
    if not game:
        return jsonify({'error': 'Pas de partie en cours'}), 400
    
    # Dealer tire jusqu'à 17
    while hand_total(game['dealer_hand']) < 17:
        game['dealer_hand'].append(game['deck'].pop())
    
    player_total = hand_total(game['player_hand'])
    dealer_total = hand_total(game['dealer_hand'])
    bet = game['bet']
    
    # Déterminer le résultat
    if player_total > 21:
        result = 'lose'
        profit = -bet
    elif dealer_total > 21 or player_total > dealer_total:
        result = 'win'
        profit = bet
    elif player_total < dealer_total:
        result = 'lose'
        profit = -bet
    else:
        result = 'draw'
        profit = 0
    
    # Mettre à jour l'argent
    if result == 'win':
        current_user.add_money(bet * 2)
    elif result == 'draw':
        current_user.add_money(bet)
    
    # Sauvegarder l'historique
    history = GameHistory(
        user_id=current_user.id,
        game_type='blackjack',
        bet_amount=bet,
        result=result,
        profit=profit,
        multiplier=1.0 if result == 'win' else 0,
        details={'player_total': player_total, 'dealer_total': dealer_total}
    )
    db.session.add(history)
    db.session.commit()
    
    session.pop('blackjack', None)
    
    return jsonify({
        'result': result,
        'profit': profit,
        'money': current_user.money,
        'dealer_hand': game['dealer_hand'],
        'dealer_total': dealer_total,
        'stats': get_global_stats()
    })

# ============================================
# ROULETTE
# ============================================

@app.route('/api/roulette/spin', methods=['POST'])
@login_required
def roulette_spin():
    """Faire tourner la roulette"""
    data = request.json
    bet = int(data.get('bet', 50))
    mode = data.get('mode', 'color')
    choice = data.get('choice')
    
    if bet < 10:
        return jsonify({'error': 'Mise minimum : 10$'}), 400
    
    if bet > current_user.money:
        return jsonify({'error': 'Mise trop élevée'}), 400
    
    current_user.remove_money(bet)
    
    # Générer le numéro
    number = random.randint(0, 36)
    
    # Déterminer la couleur
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    if number == 0:
        color = 'Green'
    elif number in red_numbers:
        color = 'Red'
    else:
        color = 'Black'
    
    # Déterminer le résultat
    if mode == 'color':
        won = (choice == color)
        multiplier = 2 if won else 0
    else:
        won = (int(choice) == number)
        multiplier = 35 if won else 0
    
    result = 'win' if won else 'lose'
    profit = (bet * multiplier) - bet if won else -bet
    
    if won:
        current_user.add_money(bet * multiplier)
    
    # Sauvegarder l'historique
    history = GameHistory(
        user_id=current_user.id,
        game_type='roulette',
        bet_amount=bet,
        result=result,
        profit=profit,
        multiplier=multiplier,
        details={'number': number, 'color': color, 'choice': choice}
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({
        'result': result,
        'number': number,
        'color': color,
        'profit': profit,
        'money': current_user.money,
        'stats': get_global_stats()
    })

# ============================================
# MINEBOMB
# ============================================

@app.route('/api/minebomb/start', methods=['POST'])
@login_required
def minebomb_start():
    """Démarrer MineBomb"""
    data = request.json
    bet = int(data.get('bet', 50))
    bombs = int(data.get('bombs', 5))
    
    if bet < 10:
        return jsonify({'error': 'Mise minimum : 10$'}), 400
    
    if bet > current_user.money:
        return jsonify({'error': 'Mise trop élevée'}), 400
    
    if bombs < 3 or bombs > 10:
        return jsonify({'error': 'Entre 3 et 10 bombes'}), 400
    
    current_user.remove_money(bet)
    
    # Créer la grille
    grid = ['safe'] * (25 - bombs) + ['bomb'] * bombs
    random.shuffle(grid)
    
    session['minebomb'] = {
        'bet': bet,
        'bombs': bombs,
        'grid': grid,
        'revealed': [],
        'diamonds_found': 0
    }
    
    return jsonify({'money': current_user.money})

@app.route('/api/minebomb/reveal', methods=['POST'])
@login_required
def minebomb_reveal():
    """Révéler une case"""
    data = request.json
    index = int(data.get('index'))
    
    game = session.get('minebomb')
    if not game:
        return jsonify({'error': 'Pas de partie en cours'}), 400
    
    cell_type = game['grid'][index]
    game['revealed'].append(index)
    
    if cell_type == 'bomb':
        # Perdu
        history = GameHistory(
            user_id=current_user.id,
            game_type='minebomb',
            bet_amount=game['bet'],
            result='lose',
            profit=-game['bet'],
            multiplier=0,
            details={'bombs': game['bombs'], 'diamonds': game['diamonds_found']}
        )
        db.session.add(history)
        db.session.commit()
        
        session.pop('minebomb', None)
        
        return jsonify({
            'type': 'bomb',
            'money': current_user.money,
            'grid': game['grid'],
            'stats': get_global_stats()
        })
    
    else:
        # Diamant trouvé
        game['diamonds_found'] += 1
        
        # Calculer le multiplicateur
        safe_cells = 25 - game['bombs']
        diamonds = game['diamonds_found']
        multiplier = 1 + (diamonds * 0.3 * (game['bombs'] / 5))
        potential_win = int(game['bet'] * multiplier)
        
        session['minebomb'] = game
        
        return jsonify({
            'type': 'diamond',
            'multiplier': multiplier,
            'potential_win': potential_win,
            'diamonds_found': diamonds
        })

@app.route('/api/minebomb/cashout', methods=['POST'])
@login_required
def minebomb_cashout():
    """Encaisser les gains"""
    game = session.get('minebomb')
    if not game:
        return jsonify({'error': 'Pas de partie en cours'}), 400
    
    diamonds = game['diamonds_found']
    multiplier = 1 + (diamonds * 0.3 * (game['bombs'] / 5))
    winnings = int(game['bet'] * multiplier)
    profit = winnings - game['bet']
    
    current_user.add_money(winnings)
    
    history = GameHistory(
        user_id=current_user.id,
        game_type='minebomb',
        bet_amount=game['bet'],
        result='win',
        profit=profit,
        multiplier=multiplier,
        details={'bombs': game['bombs'], 'diamonds': diamonds}
    )
    db.session.add(history)
    db.session.commit()
    
    session.pop('minebomb', None)
    
    return jsonify({
        'profit': profit,
        'multiplier': multiplier,
        'money': current_user.money,
        'stats': get_global_stats()
    })

# ============================================
# SLOTS
# ============================================

@app.route('/api/slots/spin', methods=['POST'])
@login_required
def slots_spin():
    """Faire tourner les slots"""
    data = request.json
    bet = int(data.get('bet', 50))
    
    if bet < 10:
        return jsonify({'error': 'Mise minimum : 10$'}), 400
    
    if bet > current_user.money:
        return jsonify({'error': 'Mise trop élevée'}), 400
    
    current_user.remove_money(bet)
    
    symbols = ['🎰', '🍋', '🍊', '🍇', '7️⃣', '💎']
    reels = [random.choice(symbols) for _ in range(3)]
    
    # Déterminer le résultat
    if reels[0] == reels[1] == reels[2]:
        # 3 identiques
        multipliers = {
            '💎': 100,
            '7️⃣': 50,
            '🎰': 20,
            '🍋': 15,
            '🍊': 12,
            '🍇': 10
        }
        multiplier = multipliers.get(reels[0], 10)
        result = 'win'
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        # 2 identiques
        multiplier = 2
        result = 'win'
    else:
        # Perdu
        multiplier = 0
        result = 'lose'
    
    profit = (bet * multiplier) - bet if result == 'win' else -bet
    
    if result == 'win':
        current_user.add_money(bet * multiplier)
    
    history = GameHistory(
        user_id=current_user.id,
        game_type='slots',
        bet_amount=bet,
        result=result,
        profit=profit,
        multiplier=multiplier,
        details={'reels': reels}
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({
        'result': result,
        'reels': reels,
        'multiplier': multiplier,
        'profit': profit,
        'money': current_user.money,
        'stats': get_global_stats()
    })

# ============================================
# HISTORIQUE
# ============================================

@app.route('/api/history')
@login_required
def get_history():
    """Récupère l'historique des 20 dernières parties"""
    games = GameHistory.query.filter_by(user_id=current_user.id)\
        .order_by(GameHistory.played_at.desc())\
        .limit(20)\
        .all()
    
    return jsonify([{
        'id': g.id,
        'game_type': g.game_type,
        'bet': g.bet_amount,
        'result': g.result,
        'profit': g.profit,
        'multiplier': g.multiplier,
        'date': g.played_at.isoformat()
    } for g in games])

# ============================================
# INITIALISATION
# ============================================

def init_db():
    """Initialise la base de données"""
    with app.app_context():
        db.create_all()
        
        if Achievement.query.count() == 0:
            achievements = [
                Achievement(name='Premier pas', description='Joue ta première partie', icon='🎮', reward=100),
                Achievement(name='Gagnant', description='Gagne 10 parties', icon='🏆', reward=500),
                Achievement(name='Chanceux', description='Gagne avec un multiplicateur x50+', icon='🍀', reward=1000),
                Achievement(name='Millionnaire', description='Atteins 10,000$', icon='💰', reward=2000),
                Achievement(name='Série de victoires', description='Gagne 5 parties d\'affilée', icon='🔥', reward=1500),
            ]
            db.session.add_all(achievements)
            db.session.commit()
            print("✅ Achievements créés")

init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)