import random
import numpy as np
import math
import time

#This .py defines actions the Agent may take at an atomic level, as opposed to
#macro level decisions (i.e that may involve graph pathing algorithms)

#is_legal here is expected to check if something is physically possible.
#the legality of WHEN an action is taken is left in the responsibility of the
#simulation calling these methods


#rolls the dice X,Y times and subsorts the dice rolls in a manner congruent with
#risk dice rolling. I.e, 3 attacker and 2 defender dice per battle if there
#are enough troops to do so.
def get_dice_rolls(attacker_troops, defender_troops, verbose=False):

    attacker_dice_count = min(3, attacker_troops)
    defender_dice_count = min(2, defender_troops)

    attacker_rolls = np.random.randint(1, 7, attacker_dice_count)
    attacker_rolls = sorted(attacker_rolls, reverse = True)

    defender_rolls = np.random.randint(1, 7, defender_dice_count)
    defender_rolls = sorted(defender_rolls, reverse = True)

    if verbose:
        print("\nAttacker rolls: " + str(attacker_rolls))
        print("Defender rolls: " + str(defender_rolls))

    return attacker_rolls, defender_rolls

# If there are a lot of troops that are going to battle, roll the dice many times ahead of time
def get_dice_bag(attacker_troops, defender_troops, verbose=False):

    low = min(attacker_troops, defender_troops)
    bag_size = low * 5
    attacker_dice = low * 3
    defender_dice = low * 2

    dice_rolls = np.random.randint(1, 7, bag_size)

    #https://stackoverflow.com/questions/3668930/sorting-a-sublist-within-a-python-list-of-integers
    # sort every group of 3 in the attacker's portion
    for i in range(0, attacker_dice, 3):
        dice_rolls[i:i+3] = sorted(dice_rolls[i:i+3], reverse=True)

    # sort every group of 2 in the defender's portion
    for i in range(attacker_dice, attacker_dice+defender_dice, 2):
        dice_rolls[i:i+2] = sorted(dice_rolls[i:i+2], reverse=True)

    attacker_rolls = dice_rolls[:attacker_dice]
    defender_rolls = dice_rolls[attacker_dice:]

    if(verbose):
        print("")
        print("Attacker rolls: " + str(attacker_rolls))
        print("Defender rolls: " + str(defender_rolls))

    return attacker_rolls, defender_rolls, bag_size


#if the Agent wants to attack territory B from territory A, what happens?
#this function is complicated/convoluted and could be improved
def attack_territory(from_territory, to_territory, troops_to_attack_with, verbose=False):
    is_legal = False
    troops_lost_attacker = 0
    troops_lost_defender = 0
    attacker_won = False
    defender_troops = to_territory.troop_count

    pre_battle_troops = (from_territory.troop_count, to_territory.troop_count) #track how many troops get lost


    if (verbose): print("attack_territory " + to_territory.name + " from " + from_territory.name + " requested with " + str(troops_to_attack_with) + " troops")

    #confirm territories are directly connected
    if(to_territory.name not in from_territory.neighbor_names):
        if(verbose): print("attack_territory requsted for non-adjacent territories")
        return troops_lost_attacker, troops_lost_defender, attacker_won, is_legal
    if(from_territory.owner_color == to_territory.owner_color):
        if(verbose): print("attack_territory requested for players own territory")
        return troops_lost_attacker, troops_lost_defender, attacker_won, is_legal

    # A territory cannot have less than 1 troop. When an attack is made, 1 troop
    # less than the total troops are usable. However, this is arguably invalid more so than illegal
    if from_territory.troop_count < 2:
        if(verbose): print("attack_territory was requested, but not enough available troops to make any attack")
        return troops_lost_attacker, troops_lost_defender, attacker_won, is_legal

    is_legal = True
    if (troops_to_attack_with >= from_territory.troop_count):
        troops_to_attack_with = from_territory.troop_count - 1 # attack with at most 1 less troop than in the territory
        if(verbose): print("Attacking with troops: " + str(troops_to_attack_with))

    # attacker rolls their dice and so does defender. the highest dice
    # are compared from both attacker and defender. the defender wins ties.
    # for each dice roll won, the opponent loses 1 troop. the attacker can then
    # choose to continue rolling dice or not. Here, the attacker fully commits
    # as many troops as have been passed into the function, allowing to vectorize
    # the dice rolling process for efficiency

    # 3 v 2 dice are rolled unless the attacker doesnt have at least 3 troops
    # or the defender doesnt have at least 2 troops

    bag_size = 0
    i = 0
    j = 0
    while defender_troops > 0 and troops_to_attack_with > 0:

        attacker_dice = min(3, troops_to_attack_with)
        defender_dice = min(2, defender_troops)
        least_dice = min(attacker_dice, defender_dice)

        if(bag_size < (defender_troops + troops_to_attack_with) and (attacker_dice + defender_dice) > 4):
            attacker_rolls, defender_rolls, bag_size = get_dice_bag(troops_to_attack_with, defender_troops, verbose)
            i = 0
            j = 0

        if(attacker_dice < 3 or defender_dice < 2):
            # if we continue to use dicebag, but dicebag generated and sorted more items than the attacker/defender should have,
            # the statistical output will favor the outcome of the player with less dice more than it should
            attacker_rolls, defender_rolls = get_dice_rolls(troops_to_attack_with, defender_troops, verbose)
            bag_size = (troops_to_attack_with + defender_troops)
            i = 0
            j = 0

        if attacker_rolls[i] > defender_rolls[j]:
            defender_troops -= 1
        else:
            troops_to_attack_with -= 1

        if least_dice > 1:
            if attacker_rolls[i + 1] > defender_rolls[j + 1]:
                defender_troops -= 1
            else:
                troops_to_attack_with -= 1
        if(verbose):
            print("Attacker Troops: " + str(troops_to_attack_with))
            print("Defender Troops: " + str(defender_troops))

        bag_size -= 5
        i +=3
        j +=2


    troops_lost_attacker = (pre_battle_troops[0] - 1) - troops_to_attack_with
    troops_lost_defender = pre_battle_troops[1] - defender_troops

    from_owner = from_territory.owner
    to_owner = to_territory.owner

    #attacker lost
    if(defender_troops != 0):
        from_territory.troop_count -= troops_lost_attacker
        to_territory.troop_count -= troops_lost_defender
    else:
        # transfer of owner occurs
        attacker_won = True

        from_territory.troop_count = 1 # transfer 100% of troops except 1 that wasn't used in attack
        to_territory.troop_count = troops_to_attack_with

        # defender losses territory
        to_owner.territories[to_territory.key] = 0
        to_owner.territory_count -= 1

        # attacker gains territory
        to_territory.owner_color = from_territory.owner_color
        to_territory.owner = from_owner

        from_owner.territories[to_territory.key] = 1
        from_owner.territory_count += 1

        assert(to_territory.owner_color == from_territory.owner_color)
        assert(to_territory.owner == from_territory.owner)

    from_owner.damage_dealt[to_owner.key] += troops_lost_defender
    to_owner.damage_received[from_owner.key] += troops_lost_defender
    from_owner.total_troops  -= troops_lost_attacker
    to_owner.total_troops -= troops_lost_defender

    if(verbose): print("")
    if(verbose): print("Results of attack_territory- Attacker troops lost: " + str(troops_lost_attacker) + "  Defender troops lost: " + str(troops_lost_defender))
    return troops_lost_attacker, troops_lost_defender, attacker_won, is_legal

def place_troops(player, territory, troops):
    # does the player have enough troops and is this territory owned by player?
    is_legal = False
    if(territory.owner == player and troops <= player.placeable_troops):
        player.total_troops += troops
        territory.troop_count += troops
        player.placeable_troops -= troops
        is_legal = True
    return is_legal

def get_troops(player, territories):
    territories_owned = [i for i, owned in enumerate(player.territories) if owned]
    territories_owned_obj = [territories[i] for i in territories_owned]
    # new_troops = max(3, len(territories_owned) // 3) # this is how it works in Risk (plus additional troops for bonuses) 
    new_troops = 3 + len(territories_owned) # this is a more aggressive version to encourage aggressive play 
    continents_map = {}
    for t in territories_owned_obj:
        continents_map[t.continent] = continents_map.get(t.continent, 0) + 1
    for cont in continents_map:
        if continents_map[cont] == len(cont.territories):
            new_troops += cont.bonus_troop_count
    player.placeable_troops += new_troops

# Get random card
# The deck of cards in Risk does correspond directly to the (42) territories on the board
def get_card(hand):
    card = random.randint(0, 43)
    hand.count += 1
    if 0 <= card < 14:
        hand.soldier += 1
    elif 14 <= card < 28:
        hand.cavalry += 1
    elif 28 <= card < 42:
        hand.artillery += 1
    else:
        hand.wild += 1

# Take card from other player if you take their last territory
def take_cards(player1, player2):
    hand1, hand2 = player1.hand, player2.hand
    hand1.artillery += hand2.artillery
    hand1.cavalry += hand2.cavalry
    hand1.soldier += hand2.soldier
    hand1.wild += hand2.wild
    hand1.count += hand2.count

#returns how many troops the Agent could get by trading
#card territory bonus omitted for simplicity
def check_cards(hand):
    # dont trade the wild for the highest trade if that can be avoided
    best_trade_uses_wild = False

    #cant trade with less than 3 cards
    if hand.count < 3:
        return 0, best_trade_uses_wild

    wild_count = hand.wild
    #check from biggest to smallest trades first
    #could do some funky logic here for efficiency but that code is ugly
    if wild_count == 0:
        if hand.artillery > 0:
            if hand.cavalry > 0:
                if hand.soldier > 0:
                    return 10, best_trade_uses_wild
        if hand.artillery > 2:
            return 8, best_trade_uses_wild
        if hand.cavalry > 2:
            return 6, best_trade_uses_wild
        if hand.soldier > 2:
            return 4, best_trade_uses_wild
    else:
        best_trade_uses_wild = True
        triple_sum = 1
        if hand.artillery > 0:
            triple_sum += 1
        if hand.cavalry > 0:
            triple_sum += 1
        if hand.soldier > 0:
            triple_sum += 1
        if triple_sum > 2:
            return 10, best_trade_uses_wild
    return 0, best_trade_uses_wild

#given a hand, trades for the highest number of possible troops
#stacking the deck as a strategy is omitted for simplicty
#
# this function is more convoluted than necessary
# should just be trade_cards(player) for maximum possible troops
def trade_cards(player, troops_to_trade_for=0, uses_wild=False, already_checked_legality=False):
    hand = player.hand
    if not already_checked_legality:
        troops_to_trade_for, uses_wild = check_cards(hand)
    if troops_to_trade_for == 10:
        if not uses_wild:
            hand.artillery -= 1
            hand.cavalry -= 1
            hand.soldier -= 1
        else:
            hand.wild -= 1
            troops = [(hand.soldier, 4), (hand.cavalry, 6), (hand.artillery, 8)]
            troops = [t for t in troops if t[0] > 0]
            troops.sort()
            for i in range(2):
                if troops[i][1] == 4:
                    hand.soldier -= 1
                elif troops[i][1] == 6:
                    hand.cavalry -= 1
                else:
                    hand.artillery -= 1
        player.placeable_troops += 10
    elif troops_to_trade_for == 8:
        hand.artillery -= 3
        player.placeable_troops += 8
    elif troops_to_trade_for == 6:
        hand.cavalry -= 3
        player.placeable_troops += 6
    elif troops_to_trade_for == 4:
        hand.soldier -= 3
        player.placeable_troops += 4
    hand.count -= 3

def fortify(from_territory, to_territory, troop_count):
    if troop_count > from_territory.troop_count - 1:
        raise "You must move at most total # of troops - 1 in the territory"
    if from_territory.owner != to_territory.owner:
        raise "You cannot fortify to an unowned territory"
    from_territory.troop_count -= troop_count
    to_territory.troop_count += troop_count

if __name__ == "__main__":
    from board import create_board, create_graph, display_graph, Territory, find_shortest_path
    print("Board initialized")
    random.seed(1)
    num_players = 6
    bot_types =   [None, None, None, None, None] # debugging line
    continents, territories, players = create_board(num_players, bot_types)
    board_graph = create_graph(territories, display=False)
    display_graph(board_graph, territories, title="Initialized board", blocking_display=True)
    test_pathing = True


    index = 0
    for t in territories:
        print(t.name + ", Index: " + str(index), end=" ")
        index += 1
        if index % 5 ==0:
            print("")
    print("")
    print("")

    alaska_index = 0
    Kamchatka_index = 19
    ural_index = 16

    alaska = territories[alaska_index]
    Kamchatka = territories[Kamchatka_index]
    ural = territories[ural_index]

    print("Alaska owner: "  + str(alaska.owner_color))
    print("Kamchatka owner: " + str(Kamchatka.owner_color))


    print("Pre ownership vector of pink: " + str(alaska.owner.territories))
    alaska.troop_count = 20
    print("Pre ownership vector of red: " + str(Kamchatka.owner.territories))
    Kamchatka.troop_count = 1

    attack_territory(alaska, Kamchatka, 20, players, reduce_kurtosis=False, verbose=True)

    print("Post ownership vector of blue: " + str(alaska.owner.territories))
    print("Post ownership vector of pink: " + str(Kamchatka.owner.territories))
    for i in range(len(alaska.owner.territories)):
        if alaska.owner.territories[i] != Kamchatka.owner.territories[i]:
            print(f"The lists differ at index {i}")

    print("Alaska owner: "  + str(alaska.owner_color))
    print("Kamchatka owner: " + str(Kamchatka.owner_color))


    troop_losses_attacker = []
    troop_losses_defender = []
    attacker_wins = 0
    attackers = 11
    defenders = attackers - 1

    start_time = time.time()
    battles = 20000
    for i in range(battles):
            alaska.troop_count = attackers
            Kamchatka.troop_count = defenders
            Kamchatka.owner_color = "red"
            alaska.owner_color = "blue"
            troops_lost_attacker, troops_lost_defender, attacker_won, is_legal = attack_territory(alaska, Kamchatka, 100, players, reduce_kurtosis=False, verbose=False)
            if not is_legal:
                print("bad return value for attack_territory")
                break
            troop_losses_attacker.append(troops_lost_attacker)
            troop_losses_defender.append(troops_lost_defender)
            if attacker_won:
                attacker_wins += 1
    end_time = time.time()
    elapsed_time = end_time - start_time


    mean_troop_loses_attacker = np.mean(troop_losses_attacker)
    std_troop_loses_attacker = np.std(troop_losses_attacker)

    mean_troop_loses_defender = np.mean(troop_losses_defender)
    std_troop_loses_defender = np.std(troop_losses_defender)

    print("")
    print("Elapsed time for " + str(battles) + " attacks with " + str(attackers + defenders ) + " combined attackers and defenders: " + str(elapsed_time))
    print("The attacker won " + str(100 * (attacker_wins/battles) )+ "% of the time")

    print("Mean of troop losses for attacker: ", mean_troop_loses_attacker)
    print("Standard deviation of troop losses for attacker: ", std_troop_loses_attacker)

    print("Mean of troop losses for defender: ", mean_troop_loses_defender)
    print("Standard deviation of troop losses for defender: ", std_troop_loses_defender)


    if test_pathing:
        alaska.troop_count = attackers
        Kamchatka.troop_count = defenders
        Kamchatka.owner_color = "red"
        alaska.owner_color = "blue"
        # SHOULD EXIST
        path = find_shortest_path(board_graph, alaska, Kamchatka, alaska.owner_color, attack_turn=True, display=True)
        print("Attack path from Alaska to Kamchatka: " + str(path))
        path = find_shortest_path(board_graph, alaska, ural, alaska.owner_color, attack_turn=True, display=True)
        print("Attack path from Alaska to Ural: " + str(path))
        path = find_shortest_path(board_graph, alaska, Kamchatka, alaska.owner_color, attack_turn=False, display=True)
        # SHOULD NOT EXIST
        print("Fortify path from Alaska to Kamchatka: " + str(path))




    display_graph(board_graph, territories,title="Final board state", blocking_display=True)
