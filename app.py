import asyncio
from collections import Counter
from dataclasses import dataclass
import dataclasses
from datetime import datetime, timedelta, timezone
import random
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from persian_names import fullname_en

app = FastAPI()

@dataclass
class Cell:
    playerId: str
    START_HP: int = 5
    GOOD_SOLDIER_AGE: int = 20
    PEAK_HP_AGE: int = 20
    MAX_AGE: int = 60
    PEAK_HP: int = 20
    age: int = 0
    hp: int = 20
    lastPlayerId: str = None
    maxHP: float = 20

    def getMaxHPForAge(self):
        if self.age < self.PEAK_HP_AGE:
            return self.START_HP+((self.PEAK_HP-self.START_HP)*(self.age/self.PEAK_HP_AGE))
        else:
            return (self.PEAK_HP*(1-((self.age-self.PEAK_HP_AGE)/(self.MAX_AGE-self.PEAK_HP_AGE))))


# Test max hp for age
#print([c.getMaxHPForAge() for c in [Cell(playerId='asdf', age=x) for x in range(60)]])
#from time import sleep 
#sleep(100)

class Board:
    # 2 player
    boardData:list[list[str]] = [[]]
    boardWidth:int = 30
    boardHeight:int = 20
    currFrame:int = 0
    CONWAYS_GAME_OF_LIFE_RULES = {
        'b': [3],
        's': [2, 3]
    }
    gameOfLifeRules: dict = {
        'b': [2,3,4,5,6],
        's': [0,1,2,3,4,5,6,7,8]
    }

    #gameOfLifeRules = CONWAYS_GAME_OF_LIFE_RULES

    def __init__(self):
        self.boardData = self.getClearBoard()

    def getClearBoard(self):
        return [[Cell(playerId=None) for y in range(self.boardHeight)] for x in range(self.boardWidth)]

    def getBoardSendData(self):
        return {
            "board": {
                "currFrame": self.currFrame,
                "width": self.boardWidth,
                "height": self.boardHeight,
                "cells": [[self.boardData[x][y].__dict__ for y in range(self.boardHeight)] for x in range(self.boardWidth)]
            }
        }

    def generateTestBoard(self, playerIds):
        # Just shuffle them all lol
        self.currFrame += 1
        def getRandomCell():
            return random.choice([
                    Cell(playerId=None, age=1), 
                    Cell(playerId=random.choice(playerIds), age=1)
                ])
        self.boardData = [
                [getRandomCell()for y in range(self.boardHeight)] for x in range(self.boardWidth)
            ]
        #self.printBoardToConsole(self.boardData)

    def generateDuelBoard(self):
        self.boardData = self.getClearBoard()
        self.boardData[1][2] = Cell(playerId='ghost')
        self.boardData[2][2] = Cell(playerId='ghost2')
        self.boardData[3][2] = Cell(playerId='ghost')
        
    def countNeighbors(self, board, x, y) -> int:
        neighbors = 0
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            if x+dx >= self.boardWidth:
                continue
            if x+dx < 0:
                continue
            if y+dy >= self.boardHeight:
                continue
            if y+dy < 0:
                continue
            if board[x+dx][y+dy].playerId != None:
                neighbors += 1
        return neighbors

    def getNeighborIds(self, board, x, y) -> Counter:
        neighborPlayerIds = []
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            if x+dx >= self.boardWidth:
                continue
            if x+dx < 0:
                continue
            if y+dy >= self.boardHeight:
                continue
            if y+dy < 0:
                continue    
            if board[x+dx][y+dy].playerId != None:
                neighborPlayerIds.append(board[x+dx][y+dy].playerId)
        return Counter(neighborPlayerIds)
    
    def nextFrame(self, playerIds):
        self.currFrame += 1
        self.runGOLRuleOnBoard(self.gameOfLifeRules, playerIds)
        self.runBattleOnBoard(self.gameOfLifeRules, playerIds)
        self.applyTheInevitabilityOfDarkSweetDeath()
        
    def runGOLRuleOnBoard(self, gameOfLifeRules, playerIds):
        # Get copy of old board
        oldBoard = [row[:] for row in self.boardData]
        # Calculate new state of board
        newBoard = self.getClearBoard()
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                # Count neighbors
                numNeighbors = self.countNeighbors(oldBoard, x, y)
                if oldBoard[x][y].playerId == None:
                    # Cell was dead. Birth time?
                    if numNeighbors in gameOfLifeRules['b']:
                        # Find majority neighbor
                        neighborIds = self.getNeighborIds(oldBoard, x, y).most_common()
                        highestNeighborCountNumber = neighborIds[0][1]
                        tiedHighestNeighbors = [n[0] for n in neighborIds if n]
                        # If no majority, choose random neighbor from tied pluralities
                        newBoard[x][y] = Cell(playerId=random.choice(tiedHighestNeighbors))
                    else:
                        # Cell remains dead
                        newBoard[x][y] = dataclasses.replace(oldBoard[x][y])
                        newBoard[x][y].age += 1
                if oldBoard[x][y].playerId != None:
                    # Cell was alive. Stays alive?
                    if numNeighbors in gameOfLifeRules['s']:
                        newBoard[x][y] = dataclasses.replace(oldBoard[x][y]) # copy dict
                        newBoard[x][y].age += 1
                    else:
                        # Cell dies of loneliness
                        newBoard[x][y] = dataclasses.replace(oldBoard[x][y])
                        newBoard[x][y].age = 0
                        newBoard[x][y].playerId = None
        # Annotate board with old playerId on each cell
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                newBoard[x][y].lastPlayerId = oldBoard[x][y].playerId

        print(f'Board at frame {self.currFrame}')
        #self.printBoardToConsole(newBoard)

        self.boardData = newBoard

    def splatInNewPlayer(self, playerId):
        # Choose splat center
        splatCenterX, splatCenterY = int(random.triangular(2, self.boardWidth-1, self.boardWidth/2)), int(random.triangular(2, self.boardHeight-1, self.boardHeight/2))
        # Splat some people!
        for i in range(25):
            currX = splatCenterX + int(random.triangular(-3,3,0))
            currX = min(max(0, currX), self.boardWidth-1)
            currY = splatCenterY + int(random.triangular(-3,3,0))
            currY = min(max(0, currY), self.boardHeight-1)
            self.boardData[currX][currY] = Cell(playerId=playerId, age=Cell.GOOD_SOLDIER_AGE)

    def runBattleOnBoard(self, gameOfLifeRules, playerIds):
        print('commencing battle')
        oldBoard = [row[:] for row in self.boardData] # TODO: don't need a copy since old board is just a reference, and this copy is shallow and glitchy
        # Calculate new state of board
        newBoard = self.getClearBoard()
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                newBoard[x][y] = dataclasses.replace(oldBoard[x][y])
                if oldBoard[x][y].playerId != None:
                    neighborIds = self.getNeighborIds(oldBoard, x, y)
                    #print(f'{x=}, {y=}, {neighborIds["ghost"]=}')
                    damageTaken = 0
                    for neighbor in neighborIds:
                        if neighbor not in [oldBoard[x][y].playerId, None]:
                            damageTaken += neighborIds[neighbor]
                            #print(f'Took damage from neighbors! {neighbor=}, {damageTaken=}')
                    newBoard[x][y].hp -= damageTaken
                    if damageTaken <= 0:
                        newBoard[x][y].hp = min(int(newBoard[x][y].maxHP), newBoard[x][y].hp+1)
                if newBoard[x][y].hp <= 0:
                    newBoard[x][y] = Cell(playerId=None)
        #self.printBoardToConsole(newBoard)
        self.boardData = newBoard       

    def applyTheInevitabilityOfDarkSweetDeath(self):
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                self.boardData[x][y].maxHP = self.boardData[x][y].getMaxHPForAge()
                self.boardData[x][y].hp = min(int(self.boardData[x][y].maxHP), self.boardData[x][y].hp)
                if self.boardData[x][y].hp <= 0:
                    self.boardData[x][y] = Cell(playerId=None)

    def getPlayerTally(self, playerId):
        tally=0
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                tally+= 1 if self.boardData[x][y].playerId == playerId else 0
        return tally


    def printBoardToConsole(self, boardArray):
        for y in range(self.boardHeight):
            print( ''.join([str(boardArray[x][y].hp) if (boardArray[x][y].playerId != None) else ' ' for x in range(self.boardWidth)]) )
            #print (''.join(['*' if (boardArray[x][y]['playerId'] != None) else ' ' for x in range(self.boardWidth)]))
            #print ([str(self.countNeighbors(boardArray, x, y)) for x in range(self.boardWidth)])
            pass

    def setCell(self, x, y, playerId):
        if (x < 0) or (x >= self.boardWidth):
            return
        if (y < 0) or (y >= self.boardHeight):
            return
        self.boardData[x][y] = Cell(playerId=playerId, age=Cell.GOOD_SOLDIER_AGE)
    
@dataclass
class Player:
    playerId: str
    addCellCooldownEndTime: datetime = None

@dataclass
class Session:
    ws: WebSocket
    player: Player

playerNames = {'ghost':'AI 1'}
def getPlayers():
    return [s.player for s in sessions] + [Player(playerId="ghost")]

def resetBoard(doNotBroadcast=False):
    global board
    board = Board()
    #board.generateTestBoard([p.playerId for p in getPlayers()])
    #board.generateDuelBoard()
    #board.generateClearBoard()
    if not doNotBroadcast:
        broadcastMessage("boardReset", {})
        broadcastMessage("board", getBoardUpdateData())

sessions: list[Session] = []
board: Board
resetBoard(doNotBroadcast=True)
shutdownSignal: bool = False
timePerFrameMs = 500
numFramesPerGame = 500

def getNewFrameTime():
    return (datetime.utcnow() + timedelta(milliseconds=timePerFrameMs)).replace(tzinfo=timezone.utc).isoformat()

nextFrameTime = getNewFrameTime()





@app.get("/admin/restart")
async def doRestart():
    resetBoard()

@app.on_event("startup")
async def setup():
    asyncio.create_task(runGameLoop())

def broadcastMessage(type:str, messageData):
    messageData['type'] = type
    for session in sessions:
        async def doSendOneWSMsg(session):
            await session.ws.send_json(messageData)
        asyncio.create_task(doSendOneWSMsg(session))


def broadcastPlayersList():
    for playerId in [p.playerId for p in getPlayers()]:
        if not playerId in playerNames:
            playerNames[playerId] = fullname_en('r') # random persian name
    broadcastMessage('playerList', {'players':[p.playerId for p in getPlayers()],'playerNames':playerNames})

def getBoardUpdateData():
    boardData = board.getBoardSendData()
    boardData['board']['nextRoundTime'] = nextFrameTime
    boardData['playerTallies'] = {
        player:board.getPlayerTally(player) for player in [p.playerId for p in getPlayers()]
    }
    return boardData

async def runGameLoop():
    global board, nextFrameTime
    while not shutdownSignal:
        board.nextFrame([p.playerId for p in getPlayers()])
        nextFrameTime = getNewFrameTime()
        if board.currFrame > numFramesPerGame:
            nextFrameTime = (datetime.utcnow() + timedelta(seconds=10)).replace(tzinfo=timezone.utc).isoformat()
            broadcastMessage('lastBoard', {})
        broadcastMessage('board', getBoardUpdateData())
        if board.currFrame > numFramesPerGame:
            await asyncio.sleep(10)
            resetBoard()
        await asyncio.sleep(timePerFrameMs/1000.0)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global board

    await websocket.accept()
    playerId = uuid.uuid4().urn.split(':')[2]
    player = Player(playerId)
    thisSession = Session(ws=websocket, player=player)
    sessions.append(thisSession)
    print("Session connected")
    try:
        thisSession.playerId = playerId
        broadcastPlayersList()
        await websocket.send_json({"type":"yourPlayerInfo", "playerId":playerId})

        # Splat player cells onto board
        board.splatInNewPlayer(playerId)

        msg = getBoardUpdateData()
        msg['type'] = "board"
        await websocket.send_json(msg)
        while True:
            msg = await websocket.receive_json()
            msgType = msg['type']
            if msgType == 'addCell':
                print(msg)
                # Add cell to board
                board.setCell(msg['x'], msg['y'], thisSession.player.playerId)
                broadcastMessage('board', getBoardUpdateData())
                # Announce cooldown for clicking to client
                player.addCellCooldownEndTime = datetime.utcnow()+timedelta(seconds=10)
                await websocket.send_json({"type":"cooldownUpdate", "cooldownEndTime":player.addCellCooldownEndTime.replace(tzinfo=timezone.utc).isoformat()})
    except WebSocketDisconnect as e:
        pass # I don't care
    finally:
        sessions.remove(thisSession)
        print("Session disconnected")
        broadcastPlayersList()
    
# Must mount static files endpoint last if you don't want the other mounts above to stomp on it
app.mount("/", StaticFiles(directory="www",html=True), name="static")