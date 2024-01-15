"""
    To use this implementation, you simply have to implement `agent_function` such that it returns a legal action.
    You can then let your agent compete on the server by calling
        python3 client_simple.py path/to/your/config.json
    
    The script will keep running forever.
    You can interrupt it at any time.
    The server will remember the actions you have sent.

    Note:
        By default the client bundles multiple requests for efficiency.
        This can complicate debugging.
        You can disable it by setting `single_request=True` in the last line.
"""
import itertools
import json
import logging

import requests
import time

######################################################

class FAUhalmaGame:
    def __init__(self, state):
        self.state = state  # state is a dictionary with positions of each player's pegs
        self.move_history = []  # Stack to keep track of move history for undo functionality

    def get_legal_moves(self, player):
        """
        Generate all legal moves for a given player.
        """
        moves = []
        for peg in self.state[player]:
            is_in_goal_area=  self.is_peg_in_goal_area(peg,player)
            if not is_in_goal_area:

                # Add single-step moves
                m=self.get_adjacent_moves(peg,player)
                moves.extend(m)

                # Add jump moves
                j=self.get_jump_moves(peg,player)
                moves.extend(j)
        s = []
        for i in moves:
            if i not in s:
                s.append(i)
        return s        
    

    def get_adjacent_moves(self, peg,player):

        # Defining possible moves 
        directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        adjacent_moves = [[peg[0] + dx, peg[1] + dy] for dx, dy in directions]
        get_adjacent_moves=[]
        is_current_peg_in_goal_area=self.is_peg_in_goal_area(peg,player)
        for move in adjacent_moves:
            is_spot_empty=self.is_spot_empty(move)
            is_swap_move=self.is_swap_move(peg,move,player)
            if (is_spot_empty or is_swap_move) and self.is_spot_in_board(move):

                if is_current_peg_in_goal_area :
                    if  self.is_peg_in_goal_area(move,player):
                         get_adjacent_moves.append([peg,move])
                else :
                    
                    if not self.is_peg_in_starting_area(move,player):
                        get_adjacent_moves.append([peg,move])


        return get_adjacent_moves

        '''
        if self.is_peg_in_goal_area((peg[0],peg[1]),'A'):
            return [(peg,move) for move in adjacent_moves if self.is_spot_empty(move) and self.is_spot_in_board(move) and self.is_peg_in_goal_area((move[0],move[1]),'A') ]
        return [(peg,move) for move in adjacent_moves if self.is_spot_empty(move) and self.is_spot_in_board(move) ]
        '''

    def get_adjacent_moves2(self, peg,player, visited=None,firstpeg=None):
        
        if visited is None:
            visited = set()
        peg_tuple = tuple(peg)  # Convert peg position to tuple
        visited.add(peg_tuple)

        directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        adjacent_moves = [[peg[0] + dx, peg[1] + dy] for dx, dy in directions]
        get_adjacent_moves=[]
        is_current_peg_in_goal_area=self.is_peg_in_goal_area(peg,player)
        for move in adjacent_moves:
            is_spot_empty=self.is_spot_empty(move)
            is_swap_move=self.is_swap_move(peg,move,player)
            if (is_spot_empty or is_swap_move) and self.is_spot_in_board(move)  and tuple(move) not in visited:
                if firstpeg==None:
                        source=peg
                        firstpeg=peg
                        
                else:
                        source=firstpeg
                if is_current_peg_in_goal_area :
                    if  self.is_peg_in_goal_area(move,player):
                        le=len(list(visited))
                        if le<=2:
                            get_adjacent_moves.append([[source[0],source[1]],move])
                            Hop_chain=self.get_adjacent_moves(move, player, visited,firstpeg)
                            get_adjacent_moves.extend(Hop_chain)
                else :
                    
                    if not self.is_peg_in_starting_area(move,player):
                        le=len(list(visited))
                        if le<=2:
                            get_adjacent_moves.append([[source[0],source[1]],move])
                            Hop_chain=self.get_adjacent_moves(move, player, visited,firstpeg)
                            get_adjacent_moves.extend(Hop_chain)


        return get_adjacent_moves
    def is_swap_move(self, from_position, to_position, player):
        
        # Logic to determine if to_position is in the player's home area and occupied by an opponent's peg
        if to_position in self.get_player_starting_areas(player):
             
            # Check if any opponent occupies the to_position

            is_spot_occupied_by_owner=self.is_spot_occupied_by_X(to_position,player)
            is_spot_occupied=self.is_spot_occupied(to_position)
            if is_spot_occupied  and  not is_spot_occupied_by_owner and player=='A':
                return True
        return False

    def get_jump_moves(self, peg, player, visited=None, path=None):
        
        #Recursively generate extended jump moves (hop chains) for a peg.
        if visited is None:
            visited = set()
        if path is None:
            path = [peg]

        jump_moves = []
        peg_tuple = tuple(peg)  # Convert peg position to tuple
        visited.add(peg_tuple)  # Mark the current peg as visited

        directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

        for dx, dy in directions:
            adjacent = [peg[0] + dx, peg[1] + dy]
            jump_over = [peg[0] + 2 * dx, peg[1] + 2 * dy]
            is_spot_empty=self.is_spot_empty(jump_over)
            is_swap_move=self.is_swap_move(peg,jump_over,player)
            is_spot_occupied= self.is_spot_occupied(adjacent)
            if is_spot_occupied and (is_spot_empty or is_swap_move) and self.is_spot_in_board(jump_over) and tuple(jump_over) not in visited:
                firstp=path[0]
                is_current_peg_in_goal_area=self.is_peg_in_goal_area([firstp[0],firstp[1]],player)
                if (is_current_peg_in_goal_area and self.is_peg_in_goal_area(jump_over,player) ) or (not is_current_peg_in_goal_area and not self.is_peg_in_starting_area(jump_over,player)):
                    new_path = path + [jump_over]
                    jump_moves.append(new_path)
                    # Extend jump moves recursively
                    jump_moves.extend(self.get_jump_moves(jump_over, player, visited, new_path))

        return jump_moves
    def get_jump_moves2(self, peg, player, visited=None,firstpeg=None):
         
        if visited is None:
            visited = set()
         
        
        jump_moves = []
        Hopchain=[]
        peg_tuple = tuple(peg)  # Convert peg position to tuple
        visited.add(peg_tuple)
        directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

        for dx, dy in directions:
            adjacent = [peg[0] + dx, peg[1] + dy]
            jump_over = [peg[0] + 2 * dx, peg[1] + 2 * dy]
            is_spot_empty=self.is_spot_empty(jump_over)
            is_swap_move=self.is_swap_move(peg,jump_over,player)

            if self.is_spot_occupied(adjacent) and (is_spot_empty or is_swap_move) and self.is_spot_in_board(jump_over) and tuple(jump_over) not in visited:
                #source=list(visited)[0]
                #source = next(iter(visited))
                if firstpeg==None:
                        source=peg
                        firstpeg=peg
                else:
                        source=firstpeg
                is_current_peg_in_goal_area=self.is_peg_in_goal_area([source[0],source[1]],player)
                if (is_current_peg_in_goal_area and self.is_peg_in_goal_area(jump_over,player) ) or (not is_current_peg_in_goal_area and not self.is_peg_in_starting_area(jump_over,player)):

                     
                    
                    le=len(list(visited))

                    if le>=2:
                        print(2)
                    #jump_moves.append([[source[0],source[1]],jump_over])
                    jump_moves.append([peg,jump_over])
                    Hopchain=self.get_jump_moves(jump_over, player, visited,firstpeg)
                    jump_moves.extend(Hopchain)                   
                    Hopchain.extend(Hopchain)
                    #ss=self.get_adjacent_moves(jump_over,player)
                    #for m in ss:
                    #    tm=m[1]
                        #   jump_moves.append([[source[0],source[1]],[tm[0],tm[1]]])
                        


        return jump_moves ,Hopchain



    def is_spot_empty(self, spot):
        
        #Check if a spot on the board is empty.
        
        return not any(spot in self.state[player] for player in self.state)
    def is_spot_in_board(self, spot):       
        #Check if a spot on the board is valid.
        
         board=self.game_board()
         if spot in board:
             return True
         else:
             return False

    def game_board(self):

        if shape=='star':
            return [
                     [-3, 3], [-2, 3], [-1, 3],[0, 3],
                     [-3, 2], [-2, 2], [-1, 2],[0, 2],[1, 2],
                     [-3, 1], [-2, 1], [-1, 1],[0, 1],[1, 1],[2, 1],
                     [-3, 0], [-2, 0], [-1, 0],[0, 0],[1, 0],[2, 0],[3, 0],
                     [-2, -1], [-1, -1],[0, -1],[1, -1],[2, -1],[3,-1],
                     [-1, -2],[0, -2],[1, -2],[2, -2],[3,-2],
                     [0, -3],[1, -3],[2, -3],[3,-3],
                     
                     [-3, 6],
                     [-3, 5], [-2, 5],
                     [-3, 4], [-2, 4], [-1, 4],


                     [3, -6],
                     [3, -5], [2,-5],
                     [3, -4], [2, -4], [1, -4],

                     [-6, 3],
                     [-5, 3], [-5,2],
                     [-4, 3], [-4, 2], [-4, 1],

                     [3, 3],
                     [2, 3], [3,2],
                     [1, 3], [2, 2], [3, 1],
                     
                     [-3, -3],
                     [-2, -3], [-3, -2],
                     [-1, -3], [-2, -2],[-3, -1],

                     [6, -3],
                     [5, -2],[5, -3],
                     [4, -3],[4, -2],[4, -1]

                     ]
        elif shape=='rhombus':
            return [
                    [-3, 6],
                     [-3, 5], [-2, 5],
                     [-3, 4], [-2, 4], [-1, 4],

                     [-3, 3], [-2, 3], [-1, 3],[0, 3],
                     [-3, 2], [-2, 2], [-1, 2],[0, 2],[1, 2],
                     [-3, 1], [-2, 1], [-1, 1],[0, 1],[1, 1],[2, 1],
                     [-3, 0], [-2, 0], [-1, 0],[0, 0],[1, 0],[2, 0],[3, 0],
                     [-2, -1], [-1, -1],[0, -1],[1, -1],[2, -1],[3,-1],
                     [-1, -2],[0, -2],[1, -2],[2, -2],[3,-2],
                     [0, -3],[1, -3],[2, -3],[3,-3],

                     [3, -4], [2, -4], [1, -4],
                     [3, -5], [2,-5],
                     [3, -6]                  
                     
                     ]
    
    def is_spot_occupied_by_X(self, spot,player):
        list=self.state[player]
        if spot in list:
             return True 
        return False
    def is_spot_occupied_by_A(self, spot):
        list=self.state['A']
        if spot in list:
             return True 
        return False

    
    def is_spot_occupied_by_B(self, spot):
        list=self.state['B']
        if spot in list:
             return True 
        return False   

    def is_spot_occupied_by_C(self, spot):
        if player_num!=3:
            return False
        
        list=self.state['C']
        if spot in list:
             return True 
        return False   
    
    def is_spot_occupied(self, spot):
       
        #Check if a spot on the board is occupied.
        
        return any(spot in self.state[player] for player in self.state)
    
    def is_peg_in_goal_area(self, peg, player):
        
        #Check if a peg is in the goal area for the player.
         
        # Define the goal areas for each player
        goal_areas = {
            'A': self.get_player_goal_areas('A'),
            'B': self.get_player_goal_areas('B'),
            'C': self.get_player_goal_areas('C')
        }

        return peg in goal_areas.get(player, [])    
    def is_peg_in_starting_area(self, peg, player):
        
        #Check if a peg is in the goal area for the player.
        
        # Define the goal areas for each player
        goal_areas = {
            'A': self.get_player_starting_areas('A'),
            'B': self.get_player_starting_areas('B'),
            'C': self.get_player_starting_areas('C')
        }

        return peg in goal_areas.get(player, [])
    
    def apply_move(self, player, move):
         
        #Apply a move and update the game state.
        
        from_position, to_position = move
        # Ensure that the move is legal before applying it
        is_spot_empty=self.is_spot_empty(to_position)
        
        s=self.state[player]
        if [from_position[0],from_position[1]] in s and is_spot_empty :
            self.state[player].remove(from_position)
            self.state[player].append(to_position)
            self.move_history.append((player, from_position, to_position))  # Record the move
        else:
            raise ValueError(f"Invalid move: {move} for player {player}")

    def undo_move(self):
         
        #Revert the game state to the previous state.
        
        if self.move_history:
            player, from_position, to_position = self.move_history.pop()
            self.state[player].remove(to_position)
            self.state[player].append(from_position)  # Move the peg back to its original position

    def is_game_over(self):
         
       # Check if the game has ended.
        
        # The game is over if all pegs of a player are in their goal area
        for player in self.state:
            if not all(self.is_peg_in_goal_area(peg, player) for peg in self.state[player]):
                return False
        return True


    def is_endgame(self):
        # Example criterion: the game is in endgame if Player A has only a few pegs left to move into the goal area
        pegs_in_goal = sum(self.is_peg_in_goal_area(peg, 'A') for peg in self.state['A'])
        pegs_remaining = len(self.state['A']) - pegs_in_goal
        return pegs_remaining <= 3
    
    
    def evaluate_state(self):
        
        #Evaluate the game state considering various strategic factors.
        
        score = 0
        total_distance_to_goal = 0
        pegs_in_goal = 0
        opponent_pegs_in_goal = 0
        jump_opportunities = 0
        opponent_jump_opportunities = 0

        # Iterate through all pegs of each player
        for player in self.state:
            for peg in self.state[player]:
                distance_to_goal = self.calculate_distance_from_goal(peg, player)
                in_goal_area = self.is_peg_in_goal_area(peg, player)
                can_jump = self.can_jump(peg, player)

                if player == 'A':
                    total_distance_to_goal += distance_to_goal
                    if in_goal_area:
                        pegs_in_goal += 1
                    if can_jump:
                        jump_opportunities += 1
                else:
                    if in_goal_area:
                        opponent_pegs_in_goal += 1
                    if can_jump:
                        opponent_jump_opportunities += 1

        # Scoring for AI's pegs
        score += pegs_in_goal * 100  # Reward for each peg in the goal area
        score -= total_distance_to_goal  # Penalize based on total distance to goal
        score += jump_opportunities * 10  # Reward for jump opportunities

        # Scoring for opponent's pegs
        score -= opponent_pegs_in_goal * 50  # Penalize for each opponent peg in goal area
        score -= opponent_jump_opportunities * 10  # Penalize for opponent's jump opportunities

        return score
    def evaluate_state11(self):
         
        #Evaluate the game state from the perspective of player A, focusing on goal-area progress, jump moves, and even spread of pegs.
         
        score = 0
        peg_distances = []  # Store distances of all pegs from the goal for Player A
        in_endgame = self.is_endgame()
        for player in self.state:
            for peg in self.state[player]:
                distance_to_goal = self.calculate_distance_from_goal(peg, player)
                in_goal_area = self.is_peg_in_goal_area(peg, player)
                can_jump = self.can_jump(peg, player)
                
                if player == 'A':
                    if in_goal_area:
                        score += 100
                    else:
                        score += (30 - distance_to_goal)

                    if in_endgame:
                        # In endgame, give extra weight to reducing distance to the goal for remaining pegs
                        score += (50 - distance_to_goal) 

                    # Reward for having jump opportunities
                    if can_jump:
                        score += 10

                    # Keep track of distances for Player A's pegs
                    peg_distances.append(distance_to_goal)

                else:
                    # Scoring for opponents
                    score -= (10 - distance_to_goal)
                    if in_goal_area:
                        score -= 50  # Penalty if opponent peg is in goal area
                    if in_endgame:
                     # In endgame, penalize opponent's progress more heavily
                         score -= (20 - distance_to_goal)
                        
                    if can_jump:
                        score -= 10  # Penalty if opponent has jump opportunities

        # Encourage even spread of Player A's pegs
        if peg_distances:
            max_distance = max(peg_distances)
            min_distance = min(peg_distances)
            distance_range = max_distance - min_distance
            score -= distance_range * 5  # Penalize large disparities in peg distances

        return score
    def evaluate_state1(self):
         
        #Evaluate the game state with a focus on both reaching the goal area quickly and moving pegs evenly.
         
        score = 0
        peg_distances = []  # Store distances of all pegs from the goal

        for player in self.state:
            for peg in self.state[player]:
                distance_to_goal = self.calculate_distance_from_goal(peg, player)
                peg_distances.append(distance_to_goal)

                if player == 'A':
                    if self.is_peg_in_goal_area(peg, player):
                        score += 100  # High reward for pegs in the goal area
                    else:
                        score += (30 - distance_to_goal)  # Reward for moving closer to the goal
                else:
                    # Scoring for opponents
                    #score -= (10 - distance_to_goal)
                    
                    score -= (30 - distance_to_goal)  # Penalize opponent's progress
                    if self.is_peg_in_goal_area(peg, player):
                        score -= 80  # Additional penalty for opponent pegs in the goal area
                    if self.can_jump(peg,player):
                       score -= 10  # Penalize opponent's jump opportunities
                    if self.is_blocking_opponent(peg, 'A'):
                        score -= 5  # Penalize opponent's pegs blocking player A

        # Additional scoring to encourage moving pegs evenly
        if player == 'A':
            max_distance = max(peg_distances)
            min_distance = min(peg_distances)
            distance_range = max_distance - min_distance
            score -= distance_range * 5  # Penalize large disparities in peg distances

        return score
    def evaluate_state2(self):
        
        #Evaluate the game state from the perspective of player A.
         
        score = 0
        for player in self.state:
            for peg in self.state[player]:
                distance_to_goal = self.calculate_distance_from_goal(peg, player)

                # Scoring for player A (maximizing player)
                if player == 'A':
                    score += (30 - distance_to_goal)  # Reward for being closer to the goal
                    if self.is_peg_in_goal_area(peg, player):
                        score += 80  # Additional reward for pegs in the goal area
                    #if self.can_jump(peg,player):
                    #   score += 10  # Reward for having jump opportunities
                    

                # Scoring for opponents B and C (minimizing players)
                else:
                    score -= (30 - distance_to_goal)  # Penalize opponent's progress
                    if self.is_peg_in_goal_area(peg, player):
                        score -= 80  # Additional penalty for opponent pegs in the goal area
                    if self.can_jump(peg,player):
                       score -= 10  # Penalize opponent's jump opportunities
                    if self.is_blocking_opponent(peg, 'A'):
                        score -= 5  # Penalize opponent's pegs blocking player A
                
        return score
    def evaluate_state3(self):
         
        #Evaluate the game state from the perspective of player A.
        
        score = 0
        for player in self.state:
            for peg in self.state[player]:
                distance_to_goal = self.calculate_distance_from_goal(peg, player)

                # Scoring for player A (maximizing player)
                if player == 'A':
                    score += (10 - distance_to_goal)  # Reward for being closer to the goal
                    if self.is_peg_in_goal_area(peg, player):
                        score += 20  # Additional reward for pegs in the goal area
                    #if self.can_jump(peg,player):
                     #   score += 5  # Reward for having jump opportunities
                    

                # Scoring for opponents B and C (minimizing players)
                else:
                    score -= (10 - distance_to_goal)  # Penalize opponent's progress
                    if self.is_peg_in_goal_area(peg, player):
                        score -= 20  # Additional penalty for opponent pegs in the goal area
                    #if self.can_jump(peg,player):
                     #   score -= 5  # Penalize opponent's jump opportunities
                    if self.is_blocking_opponent(peg, 'A'):
                        score -= 3  # Penalize opponent's pegs blocking player A
                
        return score
    



    
    def can_jump(self, peg,player):
         
        #Check if the peg can make a jump.
         
        for dx, dy in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]:
            adjacent = [peg[0] + dx, peg[1] + dy]
            jump_over = [peg[0] + 2*dx, peg[1] + 2*dy]
            if self.is_spot_occupied(adjacent) and self.is_spot_empty(jump_over) and self.is_spot_in_board(jump_over):
                return True
        return False

    def is_blocking_opponent(self, peg, opponent):
         
        #Check if the peg is blocking an opponent's peg.
         
        for opponent_peg in self.state[opponent]:
            if self.is_adjacent_and_between(peg, opponent_peg,opponent):
                return True
        return False

    def is_adjacent_and_between(self, peg, opponent_peg,opponent):
        
        #Check if the peg is adjacent to and potentially blocking the opponent's peg.
         
        # Assuming blocking is defined as being adjacent and directly in line with the opponent's goal area
        # This method should be adjusted according to the game's specific rules and board layout
        dx = opponent_peg[0] - peg[0]
        dy = opponent_peg[1] - peg[1]
        return (abs(dx) <= 1 and abs(dy) <= 1) and self.is_peg_closer_to_goal(peg, opponent_peg, opponent)

    def is_peg_closer_to_goal(self, peg, opponent_peg, opponent):
         
        #Check if the peg is closer to the opponent's goal than the opponent's peg.
         
        peg_distance = self.calculate_distance_from_goal(peg, opponent)
        opponent_peg_distance = self.calculate_distance_from_goal(opponent_peg, opponent)
        return peg_distance < opponent_peg_distance
    



    def evaluate_peg_position(self, peg, player):
        
        #Evaluate a peg's position for a given player.
         
        peg_score = 0
        if self.is_peg_in_goal_area(peg, player):
            peg_score += 10  # High reward for pegs in the goal area
        else:
            # Calculate distance from goal area and adjust score accordingly
             
            distance = self.calculate_distance_from_goal(peg, player)
            peg_score += max(0, 5 - distance)   

        return peg_score
    def get_player_goal_areas(self,player):

        if player=='A' :
            return [[-3,6],[-3, 5], [-2, 5], [-3, 4], [-2, 4], [-1, 4]]
        elif player=='B' and player_num==2:
            return [[3, -6],[3, -5], [2, -5], [3, -4], [2, -4], [1, -4]]

        elif player=='B' and player_num==3:
            return [[-3, -3],[-2, -3], [-3, -2],[-1, -3], [-2, -2],[-3, -1]]
        
        elif player=='C':
            return [[6, -3],[5, -2],[5, -3],[4, -3],[4, -2],[4, -1]]
        
    def get_player_starting_areas(self,player):
        if player=='A' :
            return [[3, -6],[3, -5], [2, -5], [3, -4], [2, -4], [1, -4]]
        elif player=='B' and player_num==2:
            return [[-3, 6],[-3, 5], [-2, 5],[-3, 4], [-2, 4], [-1, 4]]

        elif player=='B' and player_num==3:
            return [[3, 3],[2, 3], [3,2],[1, 3], [2, 2], [3, 1]]
        
        elif player=='C':
            return [[-6, 3],[-5, 3], [-5,2],[-4, 3], [-4, 2], [-4, 1]]

    def calculate_distance_from_goal(self, peg, player):
         
        #Calculate a peg's approximate distance from its goal area.
         
        
        goal_areas = {
            'A': self.get_player_goal_areas('A'),
            'B': self.get_player_goal_areas('B'),
            'C': self.get_player_goal_areas('C')
        }
        if player not in goal_areas:
            return 0  # If player not found 

        min_distance = float('inf')
        is_peg_in_goal_area=self.is_peg_in_goal_area(peg,player)
        if is_peg_in_goal_area:
            min_distance = float('-inf')
        for goal in goal_areas[player]:
            distance = abs(peg[0] - goal[0]) + abs(peg[1] - goal[1])
            
            if is_peg_in_goal_area:
                min_distance = max(min_distance, distance)
            else:
                min_distance = min(min_distance, distance)

        return min_distance
    


def alpha_beta_pruning_3_player(game, depth, alpha, beta, current_player):
     
    if depth == 0 or game.is_game_over():
        r=game.evaluate_state()
        return r
    
    
    next_player = {'A': 'B', 'B': 'C', 'C': 'A'}[current_player]
    if player_num==2:
        next_player = {'A': 'B', 'B': 'A'}[current_player]

    
    if current_player == 'A':  # Assuming 'A' is the first player (maximizing)
        max_eval = float('-inf')
        legal_moves=game.get_legal_moves(current_player)
        legal_moves.sort(key=lambda move: game.calculate_distance_from_goal(move[-1], current_player))
        if legal_moves==[] and all(game.is_peg_in_goal_area(peg, current_player) for peg in game.state[current_player]):
            max_eval = float('inf')
        for lmove in legal_moves:
            move=[lmove[0],lmove[-1]]
            game.apply_move(current_player, move)
            eval = alpha_beta_pruning_3_player(game, depth - 1, alpha, beta, next_player)
            game.undo_move()           
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:  # For 'B' and 'C', assuming they might have different objectives
        min_eval = float('inf')
        legal_moves=game.get_legal_moves(current_player)
        #legal_moves.sort(key=lambda move: game.calculate_distance_from_goal(move[-1], current_player))
        #if legal_moves==[] and all(game.is_peg_in_goal_area(peg, current_player) for peg in game.state[current_player]):
        #    min_eval = float('-inf')
        for lmove in legal_moves:
            move=[lmove[0],lmove[-1]]
            game.apply_move(current_player, move)
            eval = alpha_beta_pruning_3_player(game, depth - 1, alpha, beta, next_player)
            game.undo_move()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def play_game(game):
    current_player = 'A'  # Assuming Player A is the AI and starts the game
    max_depth = player_num   # Maximum depth of the search
    
    
    while not game.is_game_over():
        if current_player == 'A':  # AI's turn
            best_score = float('-inf')
            best_move = []
            best_lmove=[]
            legal_moves_player = game.get_legal_moves(current_player)
            for lmove in legal_moves_player:
                
                move=[lmove[0],lmove[-1]]
                game.apply_move(current_player, move)

                move_score = alpha_beta_pruning_3_player(game, max_depth, float('-inf'), float('inf'),current_player)
                game.undo_move()
                
                mf=move[0]
                mt=move[1]
                if game.is_peg_in_goal_area(mf,current_player) and game.is_peg_in_goal_area(mt,current_player):
                    move_score-=30
                if move_score > best_score:
                    best_score = move_score
                    best_move = move
                    best_lmove= lmove
            
            if best_move:
                game.apply_move(current_player, best_move)               
                return best_lmove
                
                

#######################################################

def agent_function(request_dict):
     game = FAUhalmaGame(request_dict)
     best_move=play_game(game)
     print(request_dict)
     print(best_move)
     return best_move


def run(config_file, action_function, single_request=False):
    logger = logging.getLogger(__name__)

    with open(config_file, 'r') as fp:
        config = json.load(fp)
    
    logger.info(f'Running agent {config["agent"]} on environment {config["env"]}')
    logger.info(f'Hint: You can see how your agent performs at {config["url"]}agent/{config["env"]}/{config["agent"]}')

    actions = []
    for request_number in itertools.count():
        logger.debug(f'Iteration {request_number} (sending {len(actions)} actions)')
        # send request
        response = requests.put(f'{config["url"]}/act/{config["env"]}', json={
            'agent': config['agent'],
            'pwd': config['pwd'],
            'actions': actions,
            'single_request': single_request,
        })
        if response.status_code == 200:
            response_json = response.json()
            for error in response_json['errors']:
                logger.error(f'Error message from server: {error}')
            for message in response_json['messages']:
                logger.info(f'Message from server: {message}')

            action_requests = response_json['action-requests']
            if not action_requests:
                logger.info('The server has no new action requests - waiting for 1 second.')
                time.sleep(1)  # wait a moment to avoid overloading the server and then try again
            # get actions for next request
            actions = []
            print(response.json())
            for action_request in action_requests:
                print(action_request)
                actions.append({'run': action_request['run'], 'action': action_function(action_request['percept'])})
        elif response.status_code == 503:
            logger.warning('Server is busy - retrying in 3 seconds')
            time.sleep(3)  # server is busy - wait a moment and then try again
        else:
            # other errors (e.g. authentication problems) do not benefit from a retry
            logger.error(f'Status code {response.status_code}. Stopping.')
            break

shape='rhombus'
player_num=2
if __name__ == '__main__':
    

    logging.basicConfig(level=logging.INFO)
    currentgame='ws2324.1.2.3.json'

    if currentgame=='ws2324.1.2.1.json':
        shape='rhombus'
        player_num=2
    elif currentgame=='ws2324.1.2.2.json' or currentgame=='ws2324.1.2.3.json' or currentgame=='ws2324.1.2.4.json':
        shape='rhombus'
        player_num=2
    elif currentgame=='ws2324.1.2.5.json' or currentgame=='ws2324.1.2.6.json' or currentgame=='ws2324.1.2.7.json' or currentgame=='ws2324.1.2.8.json':
        shape='rhombus'
        player_num=3
    
    import sys
    #run(sys.argv[1], agent_function, single_request=False)
    run(currentgame, agent_function, single_request=True)
