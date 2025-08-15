from flask import Flask, render_template, session, redirect, request,url_for,flash
from tqdm import tqdm
import time
import json
import random
class Monster:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        # 其他属性...
    def __str__(self):
        return self.name
class Map:
    map_list = [
            {
                'map_id': 1,
                'map_name': '嘉华苑',
                'monsters': []  # 安全区，没有怪物
            },
            {
                'map_id': 2,
                'map_name': '新黄浦实验：一一班',
                'monster_list': [
                    {'monster': '毛毛虫', 'probability': 0.6},
                    {'monster': '蚂蚁', 'probability': 0.4},
                ]
            },
            # 更多地图...
        ]
    def __init__(self, map_id):
        #从map_list中读取对应的信息
        self.map_id = map_id
        self.map_name = self.map_list[map_id]['map_name']
        
        self.monster_list = self.map_list[map_id]['monster_list']  # 字典，键是怪物对象，值是遇到这个怪物的概率

    def __str__(self):
        return self.map_name

    def get_monster(self):
        # 根据概率随机选择一个怪物
        total = sum(self.monsters.values())
        rand_val = random.uniform(0, total)
        curr_sum = 0
        for monster, probability in self.monsters.items():
            curr_sum += probability
            if rand_val <= curr_sum:
                return monster
        return None
    
class Game:
    def __init__(self):
        self.level = 1  #人物等级
        self.exp = 0    #人物经验值
        self.hp = 100   #人物血量        
        self.gold = 0   #人物金币
        self.stamina = 100  #人物体力(默认为100)
        self.inventory = []
        self.pickaxes = 0
        self.pickaxe_durability = 0
        self.current_map = Map(1)

    def dig(self):
        if self.stamina >= 10:
            if 'pickaxe' in self.inventory and self.pickaxe_durability > 0:
                self.gold += 20
                self.stamina -= 5
                self.pickaxe_durability -= 1
                flash(f"你使用镐子挖到了20金币！现在你有{self.gold}金币，体力剩余{self.stamina}。镐子的耐久度剩余{self.pickaxe_durability}。")
                if self.pickaxe_durability == 0:
                    self.inventory.remove('pickaxe')
                    self.pickaxes -= 1
                    flash("你的镐子已经破损，不能再使用了。")
            else:
                self.gold += 10
                self.stamina -= 10
                flash(f"你挖到了10金币！现在你有{self.gold}金币，体力剩余{self.stamina}。")
        else:
            flash("体力不足，无法挖土。")


    def rest(self):
        flash("你开始休息...")
        for i in range(30):
            time.sleep(1)
            flash(f"休息进度：{i+1}/30")
        self.stamina += 30
        flash(f"你休息了一会儿。体力恢复到{self.stamina}。")

    def shop(self):
        item = input("你想买什么？输入'pickaxe'购买镐子，输入'food'购买食物：")
        if item == 'pickaxe' and self.gold >= 50 and self.pickaxes < 2:
            self.gold -= 50
            self.inventory.append('pickaxe')
            self.pickaxes += 1
            self.pickaxe_durability = 10
            flash("你购买了一个镐子！")
        elif item == 'food' and self.gold >= 20:
            self.gold -= 20
            self.inventory.append('food')
            flash("你购买了一些食物！")
        else:
            flash("你没有足够的金币，或者输入的物品不存在，或者你已经有两个镐子了。")


    def play(self):
        while True:
            action = input("你想做什么？挖土请输入'dig'，休息请输入'rest'，购物请输入'shop'，退出请输入'quit'：")
            if action == 'dig':
                self.dig()
            elif action == 'rest':
                self.rest()
            elif action == 'shop':
                self.shop()
            elif action == 'eat':
                self.eat()                                
            elif action == 'quit':
                break
            else:
                flash("无效的输入，请重新输入。")
    def eat(self):
        if 'food' in self.inventory:
            self.stamina += 50
            self.inventory.remove('food')
            flash(f"你吃了一些食物，体力增加了50。现在你的体力是{self.stamina}。")
        else:
            flash("你的库存中没有食物。")

    def to_dict(self):
        return {
            'gold': self.gold,
            'pickaxes': self.pickaxes,
            'pickaxe_durability': self.pickaxe_durability,
            'inventory': self.inventory,
            'stamina': self.stamina
        }

    @classmethod
    def from_dict(cls, data):
        obj = cls()
        obj.gold = data['gold']
        obj.pickaxes = data['pickaxes']
        obj.pickaxe_durability = data['pickaxe_durability']
        obj.inventory = data['inventory']
        obj.stamina = data['stamina']
        return obj
    
app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/index.html')
def index_html():
    game = Game.from_dict(session['game'])
    return render_template('index.html',  game=game )

@app.route('/')
def index():
    if 'game' not in session:
        session['game'] = Game().to_dict()
    game = Game.from_dict(session['game'])
    #获取地图列表
    maps = Map.map_list
    #获取物品列表
    item_images = {
        'pickaxe': url_for('static', filename='pickaxe.jpg'),
        'food': url_for('static', filename='food.jpg'),
        'lotus': url_for('static', filename='lotus.jpg'),
    }
    # 获取当前地图
    current_map = session.get('current_map')
    if current_map is None:
        # 设置默认地图
        current_map = Map.map_list[0]
        session['current_map'] = current_map    
    # 获取当前地图的怪物列表
    monsters = list(map(str, current_map.get('monsters', [])))
    # 其他代码...        
    return render_template('index.html', game=game , item_images = item_images , maps=maps , monsters = monsters)

@app.route('/dig', methods=['POST'])
def dig():
    game = Game.from_dict(session['game'])
    game.dig()
    session['game'] = game.to_dict()
    return redirect(url_for('index'))

@app.route('/rest', methods=['POST'])
def rest():
    game = Game.from_dict(session['game'])
    game.rest()
    session['game'] = game.to_dict()
    return redirect(url_for('index'))

@app.route('/eat', methods=['POST'])
def eat():
    game = Game.from_dict(session['game'])
    game.eat()
    session['game'] = game.to_dict()
    return redirect(url_for('index'))

@app.route('/shop.html')
def shop_html():
    game = Game.from_dict(session['game'])
    return render_template('shop.html',  game=game )

@app.route('/shop', methods=['POST'])
def shop():
    game = Game.from_dict(session['game'])
    item = request.form.get('item')
    if item == 'pickaxe' and game.gold >= 50 and game.pickaxes < 2:
        game.gold -= 50
        game.inventory.append('pickaxe')
        game.pickaxes += 1
        game.pickaxe_durability = 10
        flash("你购买了一个镐子！")
    elif item == 'food' and game.gold >= 20:
        game.gold -= 20
        game.inventory.append('food')
        flash("你购买了一些食物！")
    elif item == 'lotus' and game.gold >= 20:
        game.gold -= 20
        winnings = random.randint(0, 40)
        game.gold += winnings
        flash(f"你购买了一张彩票并赢得了 {winnings} 金币！")
    else:
        flash("你没有足够的金币，或者输入的物品不存在，或者你已经有两个镐子了。")
    session['game'] = game.to_dict()
    return redirect(url_for('index'))

@app.route('/change_map', methods=['POST'])
def change_map():
    selected_map_id = request.form.get('map_id')
    # 根据 selected_map_id 来切换地图
    for map in Map.map_list:
        if map['id'] == int(selected_map_id):
            session['current_map'] = map    #更新地图
            #怪物列表等于对应地图的怪物列表
            session['monsters'] = map.get_monster()  # 更新怪物列表
            break
    return 'OK'
if __name__ == '__main__':
    app.run(debug=True)
"""
if __name__ == '__main__':
    game = Game()
    game.play()
"""
