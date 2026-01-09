// Global variables
let currentMoney = 0;
let selectedColor = null;

// Clicker variables
let clickPower = 1;
let clickLevel = 1;
let autoLevel = 0;
let factoryLevel = 0;
let bankLevel = 0;
let passiveIncome = 0;

let clickCost = 10;
let autoCost = 50;
let factoryCost = 200;
let bankCost = 1000;

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadClickerData();
    startPassiveIncome();
});

async function loadStats() {
    try {
        const response = await fetch('/api/get_stats');
        const stats = await response.json();
        updateStatsDisplay(stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadClickerData() {
    try {
        const response = await fetch('/api/clicker/get_data');
        const data = await response.json();
        
        clickPower = data.clickPower;
        clickLevel = data.clickLevel;
        autoLevel = data.autoLevel;
        factoryLevel = data.factoryLevel;
        bankLevel = data.bankLevel;
        
        clickCost = data.clickCost;
        autoCost = data.autoCost;
        factoryCost = data.factoryCost;
        bankCost = data.bankCost;
        
        passiveIncome = data.passiveIncome;
        
        updateClickerDisplay();
    } catch (error) {
        console.error('Error loading clicker data:', error);
    }
}

// ============================================
// NAVIGATION
// ============================================
function startGame(game) {
    document.getElementById('menu').classList.remove('active');
    document.getElementById(game).classList.add('active');
}

function backToMenu() {
    document.querySelectorAll('.game-screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById('menu').classList.add('active');
}

// ============================================
// MONEY MANAGEMENT
// ============================================
function updateMoneyDisplay(money) {
    currentMoney = money;
    const display = document.getElementById('moneyDisplay');
    display.textContent = money + ' $';
    display.classList.add('pulse');
    setTimeout(() => display.classList.remove('pulse'), 500);
}

async function resetGame() {
    if (confirm('Do you really want to restart at $1000?')) {
        try {
            const response = await fetch('/api/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            const data = await response.json();
            updateMoneyDisplay(data.money);
            if (data.stats) {
                updateStatsDisplay(data.stats);
            }
            loadClickerData();
            backToMenu();
        } catch (error) {
            console.error('Reset error:', error);
        }
    }
}

// ============================================
// STATISTICS
// ============================================
function updateStatsDisplay(stats) {
    document.getElementById('totalGames').textContent = stats.totalGames;
    document.getElementById('totalWins').textContent = stats.totalWins;
    document.getElementById('totalLosses').textContent = stats.totalLosses;
    document.getElementById('biggestWin').textContent = stats.biggestWin + ' $';
    document.getElementById('biggestLoss').textContent = stats.biggestLoss + ' $';
    document.getElementById('totalWagered').textContent = stats.totalWagered + ' $';
    document.getElementById('totalWinnings').textContent = stats.totalWinnings + ' $';
    
    const winRate = stats.totalGames > 0 ? ((stats.totalWins / stats.totalGames) * 100).toFixed(1) : 0;
    document.getElementById('winRate').textContent = winRate + '%';
    
    // BlackJack stats
    document.getElementById('bjGames').textContent = stats.blackjack.games;
    document.getElementById('bjWins').textContent = stats.blackjack.wins;
    const bjWinRate = stats.blackjack.games > 0 ? ((stats.blackjack.wins / stats.blackjack.games) * 100).toFixed(1) : 0;
    document.getElementById('bjWinRate').textContent = bjWinRate + '%';
    const bjProfit = stats.blackjack.won - stats.blackjack.wagered;
    document.getElementById('bjProfit').textContent = bjProfit + ' $';
    document.getElementById('bjProfit').style.color = bjProfit >= 0 ? '#22c55e' : '#ef4444';
    
    // Roulette stats
    document.getElementById('rouletteGames').textContent = stats.roulette.games;
    document.getElementById('rouletteWins').textContent = stats.roulette.wins;
    const rouletteWinRate = stats.roulette.games > 0 ? ((stats.roulette.wins / stats.roulette.games) * 100).toFixed(1) : 0;
    document.getElementById('rouletteWinRate').textContent = rouletteWinRate + '%';
    const rouletteProfit = stats.roulette.won - stats.roulette.wagered;
    document.getElementById('rouletteProfit').textContent = rouletteProfit + ' $';
    document.getElementById('rouletteProfit').style.color = rouletteProfit >= 0 ? '#22c55e' : '#ef4444';
    
    // MineBomb stats
    document.getElementById('mbGames').textContent = stats.minebomb.games;
    document.getElementById('mbWins').textContent = stats.minebomb.wins;
    const mbWinRate = stats.minebomb.games > 0 ? ((stats.minebomb.wins / stats.minebomb.games) * 100).toFixed(1) : 0;
    document.getElementById('mbWinRate').textContent = mbWinRate + '%';
    const mbProfit = stats.minebomb.won - stats.minebomb.wagered;
    document.getElementById('mbProfit').textContent = mbProfit + ' $';
    document.getElementById('mbProfit').style.color = mbProfit >= 0 ? '#22c55e' : '#ef4444';
    
    // Slots stats
    if (stats.slots) {
        document.getElementById('slotsGames').textContent = stats.slots.games;
        document.getElementById('slotsWins').textContent = stats.slots.wins;
        const slotsWinRate = stats.slots.games > 0 ? ((stats.slots.wins / stats.slots.games) * 100).toFixed(1) : 0;
        document.getElementById('slotsWinRate').textContent = slotsWinRate + '%';
        const slotsProfit = stats.slots.won - stats.slots.wagered;
        document.getElementById('slotsProfit').textContent = slotsProfit + ' $';
        document.getElementById('slotsProfit').style.color = slotsProfit >= 0 ? '#22c55e' : '#ef4444';
    }
}

// ============================================
// MONEY CLICKER
// ============================================
async function doClick() {
    try {
        const response = await fetch('/api/clicker/click', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        updateMoneyDisplay(data.money);
        
        // Visual feedback
        const btn = document.getElementById('clickButton');
        btn.classList.add('clicked');
        setTimeout(() => btn.classList.remove('clicked'), 100);
        
        // Floating number animation
        showFloatingNumber(clickPower);
        
    } catch (error) {
        console.error('Click error:', error);
    }
}

function showFloatingNumber(amount) {
    const container = document.getElementById('floatingNumbers');
    const floatingNum = document.createElement('div');
    floatingNum.className = 'floating-number';
    floatingNum.textContent = '+' + amount + ' $';
    floatingNum.style.left = (Math.random() * 200 - 100) + 'px';
    container.appendChild(floatingNum);
    
    setTimeout(() => {
        floatingNum.remove();
    }, 2000);
}

async function buyUpgrade(type) {
    try {
        const response = await fetch('/api/clicker/upgrade', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({type})
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error);
            return;
        }
        
        const data = await response.json();
        updateMoneyDisplay(data.money);
        
        clickPower = data.clickPower;
        clickLevel = data.clickLevel;
        autoLevel = data.autoLevel;
        factoryLevel = data.factoryLevel;
        bankLevel = data.bankLevel;
        
        clickCost = data.clickCost;
        autoCost = data.autoCost;
        factoryCost = data.factoryCost;
        bankCost = data.bankCost;
        
        passiveIncome = data.passiveIncome;
        
        updateClickerDisplay();
        
    } catch (error) {
        console.error('Upgrade error:', error);
    }
}

function updateClickerDisplay() {
    document.getElementById('clickValue').textContent = clickPower;
    document.getElementById('clickLevel').textContent = clickLevel;
    document.getElementById('autoLevel').textContent = autoLevel;
    document.getElementById('factoryLevel').textContent = factoryLevel;
    document.getElementById('bankLevel').textContent = bankLevel;
    
    document.getElementById('clickCost').textContent = clickCost;
    document.getElementById('autoCost').textContent = autoCost;
    document.getElementById('factoryCost').textContent = factoryCost;
    document.getElementById('bankCost').textContent = bankCost;
    
    document.getElementById('incomeDisplay').textContent = '+' + passiveIncome + ' $/s';
}

function startPassiveIncome() {
    setInterval(async () => {
        if (passiveIncome > 0) {
            try {
                const response = await fetch('/api/clicker/passive', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                updateMoneyDisplay(data.money);
            } catch (error) {
                console.error('Passive income error:', error);
            }
        }
    }, 1000);
}

// ============================================
// BLACKJACK
// ============================================
async function startBlackjack() {
    const bet = parseInt(document.getElementById('bjBet').value);
    
    try {
        const response = await fetch('/api/blackjack/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bet})
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error);
            return;
        }
        
        const data = await response.json();
        updateMoneyDisplay(data.money);
        
        document.getElementById('bjBetting').style.display = 'none';
        document.getElementById('bjGame').style.display = 'block';
        document.getElementById('bjMessage').innerHTML = '';
        
        // Update deck info
        const totalCards = data.num_decks * 52;
        document.getElementById('deckInfo').innerHTML = `
            🎴 Playing with <strong>${data.num_decks} decks</strong> (${totalCards} cards total)
        `;
        
        displayHand('player', data.player_hand, data.player_total);
        displayHand('dealer', data.dealer_hand.slice(0, 1), '?', true);
        
        document.getElementById('hitBtn').disabled = false;
        document.getElementById('standBtn').disabled = false;
        
    } catch (error) {
        console.error('Blackjack error:', error);
        alert('Connection error');
    }
}

async function hit() {
    try {
        const response = await fetch('/api/blackjack/hit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        displayHand('player', data.player_hand, data.player_total);
        
        if (data.busted) {
            document.getElementById('hitBtn').disabled = true;
            document.getElementById('standBtn').disabled = true;
            stand();
        }
        
    } catch (error) {
        console.error('Hit error:', error);
    }
}

async function stand() {
    try {
        const response = await fetch('/api/blackjack/stand', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        displayHand('dealer', data.dealer_hand, data.dealer_total, false);
        
        const msgDiv = document.getElementById('bjMessage');
        msgDiv.className = 'message';
        
        if (data.result === 'win') {
            msgDiv.classList.add('win');
            msgDiv.innerHTML = `✅ You WIN!<br>You won ${data.profit} $`;
        } else if (data.result === 'lose') {
            msgDiv.classList.add('lose');
            msgDiv.innerHTML = `❌ You LOSE!`;
        } else {
            msgDiv.classList.add('info');
            msgDiv.innerHTML = `🤝 DRAW! Your bet has been returned.`;
        }
        
        updateMoneyDisplay(data.money);
        updateStatsDisplay(data.stats);
        
        document.getElementById('hitBtn').disabled = true;
        document.getElementById('standBtn').disabled = true;
        
        setTimeout(() => {
            document.getElementById('bjGame').style.display = 'none';
            document.getElementById('bjBetting').style.display = 'block';
        }, 3000);
        
    } catch (error) {
        console.error('Stand error:', error);
    }
}

function displayHand(player, cards, total, hideSecond = false) {
    const cardsDiv = document.getElementById(player + 'Cards');
    const totalSpan = document.getElementById(player + 'Total');
    
    cardsDiv.innerHTML = '';
    
    cards.forEach((card, index) => {
        const cardDiv = document.createElement('div');
        if (hideSecond && index === 1) {
            cardDiv.className = 'card card-back';
            cardDiv.textContent = '🂠';
        } else {
            const isRed = card.suit === '♥' || card.suit === '♦';
            cardDiv.className = 'card' + (isRed ? ' red' : '');
            cardDiv.innerHTML = card.value + '<br>' + card.suit;
        }
        cardsDiv.appendChild(cardDiv);
    });
    
    totalSpan.textContent = total;
}

// ============================================
// ROULETTE
// ============================================
function updateRouletteMode() {
    const mode = document.getElementById('rouletteMode').value;
    if (mode === 'color') {
        document.getElementById('colorMode').style.display = 'block';
        document.getElementById('numberMode').style.display = 'none';
    } else {
        document.getElementById('colorMode').style.display = 'none';
        document.getElementById('numberMode').style.display = 'block';
    }
    selectedColor = null;
    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
}

function selectColor(color) {
    selectedColor = color;
    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.classList.add('selected');
}

async function spinRoulette() {
    const bet = parseInt(document.getElementById('rouletteBet').value);
    const mode = document.getElementById('rouletteMode').value;
    
    let choice;
    if (mode === 'color') {
        if (!selectedColor) {
            alert('Please select a color!');
            return;
        }
        choice = selectedColor;
    } else {
        choice = document.getElementById('rouletteNumber').value;
    }
    
    const wheel = document.getElementById('rouletteWheel');
    wheel.classList.add('spinning');
    
    try {
        const response = await fetch('/api/roulette/spin', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bet, mode, choice})
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error);
            wheel.classList.remove('spinning');
            return;
        }
        
        const data = await response.json();
        
        setTimeout(() => {
            wheel.classList.remove('spinning');
            document.getElementById('rouletteResult').textContent = data.number;
            
            const msgDiv = document.getElementById('rouletteMessage');
            msgDiv.className = 'message';
            
            if (data.result === 'win') {
                msgDiv.classList.add('win');
                msgDiv.innerHTML = `✅ ${data.color} ${data.number}!<br>You win ${data.profit} $`;
            } else {
                msgDiv.classList.add('lose');
                msgDiv.innerHTML = `❌ ${data.color} ${data.number}<br>You lose ${bet} $`;
            }
            
            updateMoneyDisplay(data.money);
            updateStatsDisplay(data.stats);
            
            setTimeout(() => {
                msgDiv.innerHTML = '';
            }, 3000);
        }, 3000);
        
    } catch (error) {
        console.error('Roulette error:', error);
        wheel.classList.remove('spinning');
        alert('Connection error');
    }
}

// ============================================
// MINEBOMB
// ============================================
async function startMineBomb() {
    const bet = parseInt(document.getElementById('mbBet').value);
    const bombs = parseInt(document.getElementById('mbBombs').value);
    
    if (bombs < 3 || bombs > 10) {
        alert('Number of bombs must be between 3 and 10!');
        return;
    }
    
    try {
        const response = await fetch('/api/minebomb/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bet, bombs})
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error);
            return;
        }
        
        const data = await response.json();
        updateMoneyDisplay(data.money);
        
        document.getElementById('mbBetting').style.display = 'none';
        document.getElementById('mbGame').style.display = 'block';
        document.getElementById('mbMessage').innerHTML = '';
        
        document.getElementById('multiplier').textContent = '1.00';
        document.getElementById('potentialWin').textContent = '0';
        document.getElementById('bombCount').textContent = bombs;
        document.getElementById('diamondCount').textContent = '0';
        
        const grid = document.getElementById('mineGrid');
        grid.innerHTML = '';
        for (let i = 0; i < 25; i++) {
            const cell = document.createElement('div');
            cell.className = 'mine-cell';
            cell.dataset.index = i;
            cell.onclick = () => revealCell(i);
            grid.appendChild(cell);
        }
        
        document.getElementById('cashoutBtn').disabled = true;
        
    } catch (error) {
        console.error('MineBomb error:', error);
        alert('Connection error');
    }
}

async function revealCell(index) {
    const cell = document.querySelectorAll('.mine-cell')[index];
    if (cell.classList.contains('revealed')) return;
    
    try {
        const response = await fetch('/api/minebomb/reveal', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({index})
        });
        
        const data = await response.json();
        cell.classList.add('revealed');
        
        if (data.type === 'bomb') {
            cell.classList.add('bomb');
            cell.innerHTML = '💣';
            
            if (data.grid) {
                document.querySelectorAll('.mine-cell').forEach((c, i) => {
                    c.onclick = null;
                    if (data.grid[i] === 'bomb' && !c.classList.contains('revealed')) {
                        setTimeout(() => {
                            c.classList.add('revealed', 'bomb');
                            c.innerHTML = '💣';
                        }, Math.random() * 1000);
                    }
                });
            }
            
            const msgDiv = document.getElementById('mbMessage');
            msgDiv.className = 'message lose';
            msgDiv.innerHTML = '💥 BOOM! You lost';
            
            updateMoneyDisplay(data.money);
            updateStatsDisplay(data.stats);
            
            document.getElementById('cashoutBtn').disabled = true;
            
            setTimeout(() => {
                document.getElementById('mbGame').style.display = 'none';
                document.getElementById('mbBetting').style.display = 'block';
            }, 3000);
            
        } else {
            cell.classList.add('safe');
            cell.innerHTML = '💎';
            document.getElementById('multiplier').textContent = data.multiplier.toFixed(2);
            document.getElementById('potentialWin').textContent = data.potential_win;
            document.getElementById('diamondCount').textContent = data.diamonds_found;
            document.getElementById('cashoutBtn').disabled = false;
        }
        
    } catch (error) {
        console.error('Reveal error:', error);
    }
}

async function cashout() {
    try {
        const response = await fetch('/api/minebomb/cashout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        updateMoneyDisplay(data.money);
        updateStatsDisplay(data.stats);
        
        const msgDiv = document.getElementById('mbMessage');
        msgDiv.className = 'message win';
        msgDiv.innerHTML = `💰 CASHOUT!<br>You win ${data.profit} $ (x${data.multiplier})`;
        
        document.querySelectorAll('.mine-cell').forEach(cell => {
            cell.onclick = null;
        });
        document.getElementById('cashoutBtn').disabled = true;
        
        setTimeout(() => {
            document.getElementById('mbGame').style.display = 'none';
            document.getElementById('mbBetting').style.display = 'block';
        }, 3000);
        
    } catch (error) {
        console.error('Cashout error:', error);
    }
}

// ============================================
// SLOT MACHINE
// ============================================
async function spinSlots() {
    const bet = parseInt(document.getElementById('slotsBet').value);
    const btn = document.getElementById('spinSlotsBtn');
    
    btn.disabled = true;
    
    try {
        const reel1 = document.getElementById('reel1');
        const reel2 = document.getElementById('reel2');
        const reel3 = document.getElementById('reel3');
        
        const symbols = ['🎰', '🍋', '🍊', '🍇', '7️⃣', '💎'];
        
        let count = 0;
        const interval = setInterval(() => {
            reel1.textContent = symbols[Math.floor(Math.random() * symbols.length)];
            reel2.textContent = symbols[Math.floor(Math.random() * symbols.length)];
            reel3.textContent = symbols[Math.floor(Math.random() * symbols.length)];
            count++;
            
            if (count >= 20) {
                clearInterval(interval);
            }
        }, 100);
        
        const response = await fetch('/api/slots/spin', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bet})
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error);
            btn.disabled = false;
            clearInterval(interval);
            return;
        }
        
        const data = await response.json();
        
        setTimeout(() => {
            clearInterval(interval);
            
            reel1.textContent = data.reels[0];
            reel2.textContent = data.reels[1];
            reel3.textContent = data.reels[2];
            
            const msgDiv = document.getElementById('slotsMessage');
            msgDiv.className = 'message';
            
            if (data.result === 'win') {
                msgDiv.classList.add('win');
                let jackpotMsg = '';
                if (data.multiplier === 100) {
                    jackpotMsg = '🎊 MEGA JACKPOT! 🎊<br>';
                } else if (data.multiplier === 50) {
                    jackpotMsg = '🎉 JACKPOT! 🎉<br>';
                }
                msgDiv.innerHTML = `${jackpotMsg}✅ ${data.reels.join(' ')}!<br>You win ${data.profit} $ (x${data.multiplier})`;
            } else {
                msgDiv.classList.add('lose');
                msgDiv.innerHTML = `❌ ${data.reels.join(' ')}<br>You lose ${bet} $`;
            }
            
            updateMoneyDisplay(data.money);
            updateStatsDisplay(data.stats);
            
            setTimeout(() => {
                msgDiv.innerHTML = '';
                btn.disabled = false;
            }, 3000);
        }, 2000);
        
    } catch (error) {
        console.error('Slots error:', error);
        alert('Connection error');
        btn.disabled = false;
    }
}