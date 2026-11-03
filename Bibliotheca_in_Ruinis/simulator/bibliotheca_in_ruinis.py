# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

import random

# %% [markdown] id="2RoSpUnPnrNp"
# 追加すること：光の概念と得点(計算のみ)・ページドローの得点（計算のみ）・感情レベルとその得点（もういい）・stockでマッチ(もういい)・速度ダイス(後で)・人数拡張（後で）
# 進捗：③ゲームシステムの不足要素追加

# %% id="JzFHuBwhrjf2"
#ダイスの値をランダムに決定
class Dice:
    # 許容する属性の一覧をクラス変数（タプル）として定義
    ATTRIBUTES = ("slash", "thrust", "blow", "guard", "avoid")
    # 攻撃ダイスと守備ダイスのグループを定義
    OFFENSIVE_ATTRIBUTES = ("slash", "thrust", "blow")
    DEFENSIVE_ATTRIBUTES = ("guard", "avoid")
        
    def __init__(self, start, end, attribute):
        self.start = start
        self.end = end
        
        # 指定された属性が許可されたメンバーであるかチェック
        if attribute not in self.ATTRIBUTES:
            raise ValueError(f"Invalid attribute '{attribute}'. Must be one of {self.ATTRIBUTES}")
        
        self.attribute = attribute
        
        # 現在の目を保持する変数を宣言し、初期値として一度サイコロを振る
        self.current_value = None
        self.roll()

    # 攻撃ダイス（斬撃・貫通・打撃）かどうかの判定
    def is_offensive(self):
        return self.attribute in self.OFFENSIVE_ATTRIBUTES

    # 守備ダイス（防御・回避）かどうかの判定
    def is_defensive(self):
        return self.attribute in self.DEFENSIVE_ATTRIBUTES

    # def roll_width(self):
    #     return [self.start, self.end]

    # self.attribute を返す関数
    def attr(self):
        return self.attribute

    # サイコロを振り、現在の目を更新してその値を返す関数
    def roll(self):
        self.current_value = random.randint(self.start, self.end)
        return self.current_value

    # 今出ている目を返す関数
    def showing(self):
        return self.current_value

    # インスタンスの文字列表現を返す関数
    def __str__(self):
        return f"Dice(Attribute: {self.attribute}, Range: [{self.start}-{self.end}], Showing: {self.current_value})"

#バトルページの型（ダイス構成、ダイス数）
class BattlePage:
    def __init__(self, name, dice_list, dec_light, inc_light, inc_page):
        self.name = name                                                        #バトルページの名前
        self.dice_list = dice_list                                              #ダイス構成
        self.dec_light = dec_light                                              #消費する光(以下3つは今のところ計算にのみ使い、実際に消費・回復はしない)
        self.inc_light = inc_light                                              #回復する光
        self.inc_page = inc_page                                                #回復するページ
    def num_of_dice(self):
        return len(self.dice_list)

#司書の型
class Librarian:
    def __init__(self, no, page_list, light, maxlight, hp, maxhp, cp, maxcp, resi_slash, resi_con_slash, resi_thrust, resi_con_thrust, resi_blow, resi_con_blow):
        self.no = no
        self.page_list = page_list                                              #保有ページのリスト
        #self.speed_dice_list = speed_dice_list                                 #保有速度ダイスのリスト(未実装)
        self.light = light
        self.minlight = 0
        self.maxlight = maxlight
        self.hp = hp
        self.minhp = 0
        self.maxhp = maxhp
        self.cp = cp
        self.mincp = 0
        self.maxcp = maxcp
        self.resi_slash = resi_slash                                            #属性耐性
        self.resi_con_slash = resi_con_slash
        self.resi_thrust = resi_thrust
        self.resi_con_thrust = resi_con_thrust
        self.resi_blow = resi_blow
        self.resi_con_blow = resi_con_blow
        self.stock = []                                                         #未使用の守備ダイス・反撃ダイスをストック(未実装)
        self.confused_turn = 0                                                  #0なら非混乱、１・２なら混乱
        self.dead = False                                                       #trueになったら死亡

#速度ダイスの型（未実装）
class SpeedDice:
  def __init__(self, speed):
    self.speed = speed
    self.page = None
    self.ini_target = None                                                      #ターン開始時の対象
    self.target = None                                                          #最終的な対象

#戦闘結果の型
class BattleResult:
  def __init__(self):
    self.damage_dealt = 0
    self.damage_received = 0
    self.confuse_dealt = 0
    self.confuse_received = 0
    self.enemy_confused = False
    self.self_confused = False
    self.enemy_dead = False
    self.self_dead = False

#戦闘結果の平均の型
class AverageResult:
  def __init__(self):
    self.ave_damage_dealt = 0
    self.ave_damage_received = 0
    self.ave_confuse_dealt = 0
    self.ave_confuse_received = 0
    self.enemy_confuse_rate = 0
    self.self_confuse_rate = 0
    self.enemy_dead_rate = 0
    self.self_dead_rate = 0
    self.save_light = 0



# %% id="0uLj12OCNtGP"
#混乱・死亡状態のチェック
def StatusCheck(librarian):
  if librarian.dead:
    return
  if librarian.hp <= 0:
    librarian.dead = True
    librarian.confused_turn = 0
    #print(librarian.no, "は死亡した！")
  elif librarian.cp <= 0:
    librarian.confused_turn = 2
    #print(librarian.no, "は混乱した！")


# %% id="HIrlOe4kWcIA"
#攻撃ダイスと守備ダイスを仕分ける（マッチ終了時、守備ダイスをストック）
def SeparateRemainingDice(librarian, page):
    attack_dice = []

    while page.dice_list:
        dice = page.dice_list.pop(0)
        # dice_att() から attr() に変更
        if dice.is_defensive():
            librarian.stock.append(dice)
        else:
            attack_dice.append(dice)

    return attack_dice



# %% id="7X-6qGeXw2K6"
#HP, CP, 光の最大値、最小値を管理
def LimitStatus(librarian):
  librarian.hp = max(librarian.minhp, min(librarian.hp, librarian.maxhp))
  librarian.cp = max(librarian.mincp, min(librarian.cp, librarian.maxcp))
  librarian.light = max(librarian.minlight, min(librarian.light, librarian.maxlight))


# %% id="l_pZBMp_qNMP"
#ステータス変更処理
def ChangeStatus(librarian, hp_change = 0, cp_change = 0, light_change = 0):
  # ステータスを変更
  librarian.hp += hp_change
  librarian.cp += cp_change
  librarian.light += light_change

  # ステータスを規定範囲内に収める
  LimitStatus(librarian)



# %% id="lydHs6KSKj05"
#ページ同士のマッチを管理
def PageMatch(librarian1, page1, librarian2, page2):

  #結果記録用
  result1 = BattleResult()
  result2 = BattleResult()

  #どちらかのダイスが無くなるまでマッチ
  while not (page1.dice_list == [] or page2.dice_list == []):                                    #x[[a,b], [c,d], [e,f]]が入る予定
    receive_damage1, receive_confuse1, receive_damage2, receive_confuse2, dice_break = DiceMatch(librarian1, page1.dice_list[0], librarian2, page2.dice_list[0])

    #BattleResultに記録
    result1.damage_dealt += receive_damage2
    result1.damage_received += receive_damage1
    result1.confuse_dealt += receive_confuse2
    result1.confuse_received += receive_confuse1

    result2.damage_dealt += receive_damage1
    result2.damage_received += receive_damage2
    result2.confuse_dealt += receive_confuse1
    result2.confuse_received += receive_confuse2

    #ダメージ反映・ステータス変更処理
    ChangeStatus(librarian1, hp_change=-receive_damage1, cp_change=-receive_confuse1)
    ChangeStatus(librarian2, hp_change=-receive_damage2, cp_change=-receive_confuse2)

    #print("1は", receive_damage1, "ダメージ、", receive_confuse1, "混乱ダメージを受けた")
    #print("2は", receive_damage2, "ダメージ、", receive_confuse2, "混乱ダメージを受けた")


    #ダイス破壊処理
    if dice_break == 0:
      del page1.dice_list[0]
      del page2.dice_list[0]
    elif dice_break == 1:
      del page1.dice_list[0]
    elif dice_break == 2:
      del page2.dice_list[0]

    #状態確認
    StatusCheck(librarian1)
    StatusCheck(librarian2)

    #死亡の場合
    if librarian1.dead:
      result1.self_dead = True
      result2.enemy_dead = True
      #print("1が死亡したため、マッチ終了")
      page1.dice_list.clear()
      librarian1.stock.clear()
      remaining_attack2 = SeparateRemainingDice(librarian2, page2)
      remaining_attack2.clear()
      break
    if librarian2.dead:
      result2.self_dead = True
      result1.enemy_dead = True
      #print("2が死亡したため、マッチ終了")
      page2.dice_list.clear()
      librarian2.stock.clear()
      remaining_attack1 = SeparateRemainingDice(librarian1, page1)
      remaining_attack1.clear()
      break

    #混乱の場合
    if librarian1.confused_turn > 0:
      result1.self_confused = True
      result2.enemy_confused = True
      #print("1は混乱したため、マッチ終了")
      page1.dice_list.clear()
      librarian1.stock.clear()
      remaining_attack2 = SeparateRemainingDice(librarian2, page2)
      OnesidedAttack(librarian2, librarian1, remaining_attack2, result2)
      break
    if librarian2.confused_turn > 0:
      result2.self_confused = True
      result1.enemy_confused = True
      #print("2は混乱したため、マッチ終了")
      page2.dice_list.clear()
      librarian2.stock.clear()
      remaining_attack1 = SeparateRemainingDice(librarian1, page1)
      OnesidedAttack(librarian1, librarian2, remaining_attack1, result1)
      break

  #マッチ終了後、片方のページに残ったダイスで一方攻撃
  if page1.dice_list:
    remaining_attack1 = SeparateRemainingDice(librarian1, page1)
    OnesidedAttack(librarian1, librarian2, remaining_attack1, result1)

  elif page2.dice_list:
    remaining_attack2 = SeparateRemainingDice(librarian2, page2)
    OnesidedAttack(librarian2, librarian1, remaining_attack2,result2)


  return librarian1, librarian2, result1, result2



# %% id="WEl9HxjONwX-"

#ダイス同士のマッチを管理
def DiceMatch(librarian1, dice1, librarian2, dice2):
  # ダイスロール（値を更新）
  dice1.roll()
  # 
  dice2.roll()

   #何ダメージ受けたか
  receive_damage_winner = 0
  receive_damage_loser = 0
  receive_confuse_winner = 0
  receive_confuse_loser = 0

  #ダイスを消費するか
  dice_break = 0                                                                #0なら両ダイス破壊、1ならダイス1だけ破壊、2ならダイス2だけ破壊

  # マッチ勝利した方を決める
  # #勝者・敗者のキャラクターを決める
  if dice1.showing() > dice2.showing():
    win = 1
    lose = 2
    winner, winner_dice = librarian1, dice1
    loser, loser_dice = librarian2, dice2
  elif dice2.showing() > dice1.showing():
    win = 2
    lose = 1
    winner, winner_dice = librarian2, dice2
    loser, loser_dice = librarian1, dice1
  else:
    return receive_damage_winner, receive_confuse_winner, receive_damage_loser, receive_confuse_loser, dice_break

  # 初期値の設定
  diff = winner_dice.showing() - loser_dice.showing()
  
  # 1. 判定ロジック：勝者と敗者のダイスタイプ（攻撃/守備）で4パターンに分類
  if winner_dice.is_offensive() and loser_dice.is_offensive():
      # 攻撃 vs 攻撃：勝った目のぶんだけ、敗者にHP・混乱ダメージ
      receive_damage_loser += winner_dice.showing()
      receive_confuse_loser += winner_dice.showing()
      
  elif winner_dice.is_offensive() and loser_dice.is_defensive():
      if loser_dice.attr() == "guard":
          # 攻撃 vs 防御：防ぎきれなかった差分だけ、敗者にHP・混乱ダメージ
          receive_damage_loser += diff
          receive_confuse_loser += diff
      elif loser_dice.attr() == "avoid":
          # 攻撃 vs 回避（ただし回避が負けた）：勝った目のぶんだけ、敗者にHP・混乱ダメージ
          receive_damage_loser += winner_dice.showing()
          receive_confuse_loser += winner_dice.showing()
          
  elif winner_dice.is_defensive() and loser_dice.is_offensive():
      if winner_dice.attr() == "guard":
          # 防御 vs 攻撃：防いだ差分だけ、敗者（攻撃側）に混乱ダメージ
          receive_confuse_loser += diff
      elif winner_dice.attr() == "avoid":
          # 回避 vs 攻撃：勝った目のぶんだけ、勝者（回避側）の混乱ダメージが回復
          # さらに回避ダイスは破壊されず再利用（負けた攻撃ダイス側を破壊）
          receive_confuse_winner -= winner_dice.showing()
          dice_break = 2 if win == 1 else 1
          
  elif winner_dice.is_defensive() and loser_dice.is_defensive():
      if winner_dice.attr() == "guard":
          # 防御 vs 防御、または 防御 vs 回避：勝った目のぶんだけ敗者に混乱ダメージ
          receive_confuse_loser += winner_dice.showing()
      elif winner_dice.attr() == "avoid":
          if loser_dice.attr() == "guard":
              # 回避 vs 防御：勝った目のぶんだけ勝者（回避側）の混乱ダメージが回復
              receive_confuse_winner -= winner_dice.showing()
          elif loser_dice.attr() == "avoid":
              # 回避 vs 回避：何も起こらない
              pass

  # 2. 耐性（レジスト）計算ロジック
  # 勝者が攻撃ダイスの場合のみ、敗者の属性耐性を適用する
  if winner_dice.is_offensive():
      att = winner_dice.attr()
      # 動的に敗者の耐性を取得して乗算
      resi_hp = getattr(loser, f"resi_{att}")
      resi_cp = getattr(loser, f"resi_con_{att}")
      
      receive_damage_loser *= resi_hp
      receive_confuse_loser *= resi_cp

  # 3. 最終的なリターン処理（librarian1, librarian2 の順に並び替えて返す）
  if win == 1:
      return receive_damage_winner, receive_confuse_winner, receive_damage_loser, receive_confuse_loser, dice_break
  else:
      return receive_damage_loser, receive_confuse_loser, receive_damage_winner, receive_confuse_winner, dice_break


# %% id="f7OFPidnRAaK"
#一方攻撃を管理
def OnesidedAttack(attacker, target, dice_list, result):

  for current_dice in dice_list:
    if attacker.dead or target.dead:
      break
      
    # 新しい仕様：ダイスを振って出目を取得
    roll = current_dice.roll()
    
    # ターゲットが混乱状態の場合（ダメージ2倍）
    if target.confused_turn > 0:
      reci_damage = roll * 2.0
      reci_confuse = roll * 2.0
    else:
      # 新しい仕様：getattrを使って動的に耐性を取得し、ifの森を解消
      att = current_dice.attr()
      # 守備ダイス（guard, avoid）が一方攻撃のリストに残っていた場合の安全弁
      if att in ("guard", "avoid"):
          reci_damage = 0
          reci_confuse = 0
      else:
          resi_hp = getattr(target, f"resi_{att}")
          resi_cp = getattr(target, f"resi_con_{att}")
          reci_damage = roll * resi_hp
          reci_confuse = roll * resi_cp

    # BattleResultに記録
    result.damage_dealt += reci_damage
    result.confuse_dealt += reci_confuse

    # ダメージ反映・ステータス変動範囲
    ChangeStatus(target, hp_change=-reci_damage, cp_change=-reci_confuse)

    # 状態確認
    StatusCheck(target)
    if target.dead:
      result.enemy_dead = True
      break
    if target.confused_turn > 0:
      result.enemy_confused = True






# %% id="_eTRd-FLR9Dq"
#ターン管理
def Turn(librarian1, librarian2):
  print("ターン開始")
  # 敵側のページは固定（今は）
  enemy_page = librarian2.page_list[0]
  # 司書１が使うページを決める
  best_page1 = SelectBestPage(librarian1, librarian2, enemy_page, 100)
  print("司書1が選択したページ:", best_page1.name)
  
  # ダイスの情報を表示する部分を修正
  for dice in best_page1.dice_list:
    # 最もシンプルな修正（attr() に変更し、最小値・最大値を直接参照）
    print(dice.attr(), [dice.start, dice.end])
    
    # もしくは、先日作った __str__ を使ってシンプルに print(dice) とするだけでも綺麗に出力されます
    # print(dice)

  # 実際にページを使う
  PageMatch(librarian1, best_page1, librarian2, enemy_page)
  print("１のHP：", librarian1.hp, "１のCP：", librarian1.cp)
  print("２のHP：", librarian2.hp, "２のCP：", librarian2.cp)

  TurnChange(librarian1, librarian2)

  print("ターン終了")


# %% id="FBQLJUa5WM59"
#ターン切り替え処理
def TurnChange(librarian1, librarian2):

  #光回復・ステータス変動処理
  ChangeStatus(librarian1, light_change=1)
  ChangeStatus(librarian2, light_change=1)

  #stockを空にする
  librarian1.stock.clear()
  librarian2.stock.clear()

  #混乱状態の更新(混乱復帰時にcp全快)
  if librarian1.confused_turn == 2:
    librarian1.confused_turn -= 1
  elif librarian1.confused_turn == 1:
    librarian1.confused_turn -= 1
    librarian1.cp = librarian1.maxcp
  if librarian2.confused_turn == 2:
    librarian2.confused_turn -= 1
  elif librarian2.confused_turn == 1:
    librarian2.confused_turn -= 1
    librarian2.cp = librarian2.maxcp


# %% id="o44-vcSZmIjj"

#仮想的にマッチを行う
import copy
def VirtualBattle(librarian1, page1, librarian2, page2, num_of_try):

  #記録用
  total_damage_dealt = 0
  total_damage_received = 0
  total_confuse_dealt = 0
  total_confuse_received = 0

  enemy_confused_count = 0
  self_confused_count = 0

  enemy_dead_count = 0
  self_dead_count = 0

  for i in range(num_of_try):
    v_librarian1 = copy.deepcopy(librarian1)
    v_librarian2 = copy.deepcopy(librarian2)
    v_page1 = copy.deepcopy(page1)
    v_page2 = copy.deepcopy(page2)

    #仮想マッチ
    v_librarian1, v_librarian2, result1, result2 = PageMatch(v_librarian1, v_page1, v_librarian2, v_page2)
    #結果を累積
    total_damage_dealt += result1.damage_dealt
    total_damage_received += result1.damage_received
    total_confuse_dealt += result1.confuse_dealt
    total_confuse_received += result1.confuse_received

    if result1.enemy_confused:
      enemy_confused_count += 1
    if result1.self_confused:
      self_confused_count += 1
    if result1.enemy_dead:
      enemy_dead_count += 1
    if result1.self_dead:
      self_dead_count += 1

  #平均値
  average_result = AverageResult()

  average_result.ave_damage_dealt = total_damage_dealt / num_of_try
  average_result.ave_damage_received = total_damage_received / num_of_try
  average_result.ave_confuse_dealt = total_confuse_dealt / num_of_try
  average_result.ave_confuse_received = total_confuse_received / num_of_try

  #確率
  average_result.enemy_confused_rate = enemy_confused_count / num_of_try
  average_result.self_confused_rate = self_confused_count / num_of_try
  average_result.enemy_dead_rate = enemy_dead_count / num_of_try
  average_result.self_dead_rate = self_dead_count / num_of_try

  #光消費・回復とページドロー
  average_result.save_light = v_librarian1.light - v_page1.dec_light + v_page1.inc_light + v_page1.inc_page

  return average_result



# %% id="qtWraMJrABLn"
#評価の得点　=　｛（与ダメージ）ー（被ダメージ）｝＋｛（与混乱ダメージ）ー（被混乱ダメージ）｝＋（混乱ボーナス/ペナルティ）＋（死亡ボーナス/ペナルティ）
def CalculateEvaluation(result):
  #重み
  weight_damage = 1.0                #与ダメ
  weight_confuse = 1.0               #与混乱ダメ
  weight_confused = 10.0             #混乱状態
  weight_dead = 10.0                 #死亡状態
  weight_light = 3.0

  evaluation = (
      weight_damage * (result.ave_damage_dealt- result.ave_damage_received)
      + weight_confuse * (result.ave_confuse_dealt- result.ave_confuse_received)
      + weight_confused * (result.enemy_confused_rate- result.self_confused_rate)
      + weight_dead * (result.enemy_dead_rate- result.self_dead_rate)
      + weight_light * result.save_light
  )

  return evaluation


# %% id="IDOAv3leCWIY"
#バトルページの評価をする
def EvaluatePage(librarian, page, enemy, enemy_page, num_of_try):
  #複数回計算
  result = VirtualBattle(librarian, page, enemy, enemy_page, num_of_try)
  #点数付け
  evaluation = CalculateEvaluation(result)
  print("評価値：", evaluation)

  return evaluation


# %% id="x0pBduRJDGil"
#計算結果から、最も良いバトルページを選択
def SelectBestPage(librarian, enemy, enemy_page, num_of_try):
  best_page = None
  best_evaluation = float('-inf')

  for page in librarian.page_list:
    if page.dec_light > librarian.light:
      print(page.name, "は光不足のため使用できない")
      continue
    evaluation = EvaluatePage(librarian, page, enemy, enemy_page, num_of_try)
    if evaluation > best_evaluation:
      print("司書", librarian.no,"ページの評価値：", evaluation)
      best_evaluation = evaluation
      best_page = page

  return best_page


# %% colab={"base_uri": "https://localhost:8080/"} id="AGSrsqd9nERU" outputId="a034fcf5-67e8-4be1-8b50-3573d539901e"
#テスト
dice1 = Dice(2, 3, "thrust")
dice2 = Dice(1, 4, "blow")

dice3 = Dice(1, 5, "avoid")
dice4 = Dice(2, 3, "guard")
dice5 = Dice(1, 2, "slash")

dice6 = Dice(3, 6, "thrust")
dice7 = Dice(2, 6, "guard")

dice8 = Dice(3, 5, "slash")
dice9 = Dice(1, 3, "thrust")

dice10 = Dice(1, 4, "thrust")

dice11 = Dice(2, 3, "thrust")
dice12 = Dice(3, 4, "guard")

dice13 = Dice(2, 6, "blow")
dice14 = Dice(2, 4, "blow")

dice15 = Dice(2, 6, "guard")
dice16 = Dice(2, 5, "guard")
dice17 = Dice(2, 6, "blow")


btp1 = BattlePage("軽い攻撃", [dice1, dice2], 1, 0, 0)
btp2 = BattlePage("軽い防御", [dice3, dice4, dice5], 1, 0, 0)
btp3 = BattlePage("攻撃と守備", [dice6, dice7], 2, 0, 0)
btp4 = BattlePage("集中攻撃", [dice8, dice8, dice9], 3, 0, 0)
btp5 = BattlePage("準備", [dice11, dice12], 1, 0, 0)



#キャラクターの作成
librarian1 = Librarian(1, [btp1, btp2, btp3, btp4], 2, 3, 30, 30, 15, 15, 1.0, 1.0, 1.5, 1.5, 2.0, 2.0)
librarian2 = Librarian(2, [btp5], 3, 3, 50, 50, 30, 30, 2.0, 1.0, 2.0, 1.0, 1.5, 1.5)


Turn(librarian1, librarian2)


