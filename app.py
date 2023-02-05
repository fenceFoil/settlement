import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import random
import uuid

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

boardPlayerIds = []

class Board:
    # 2 player
    boardPlayerIds:list[list[str]] = [[]]
    boardWidth:int = 14
    boardHeight:int = 14
    currFrame:int = 0
    CONWAYS_GAME_OF_LIFE_RULES = {
        'b': [3],
        's': [2, 3]
    }
    #gameOfLifeRules: dict = {
    #    'b': [0, 6, 7, 8],
    #    's': [2, 3, 4, 5]
    #}
    gameOfLifeRules = CONWAYS_GAME_OF_LIFE_RULES

    def getClearBoard(self):
        return [[{"playerId":None,"age":0} for x in range(self.boardWidth)] for y in range(self.boardHeight)]

    def __init__(self):
        self.boardPlayerIds = self.getClearBoard()

    def getBoardSendData(self):
        return {
            "board": {
                "currFrame": self.currFrame,
                "width": self.boardWidth,
                "height": self.boardHeight,
                "cells": self.boardPlayerIds
            }
        }

    def generateTestFrame(self, playerIds):
        # Just shuffle them all lol
        self.currFrame += 1
        def getRandomCell():
            return random.choice([
                    {"playerId":None,"age":1}, 
                    {"playerId":random.choice(playerIds),"age":1}
                ])
        self.boardPlayerIds = [
                [getRandomCell() for x in range(self.boardWidth)]
            for y in range(self.boardHeight)]
        #self.printBoardToConsole(self.boardPlayerIds)
        
    def countNeighbors(self, board, x, y):
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
            if board[x+dx][y+dy]['playerId'] != None:
                neighbors += 1
        return neighbors
        
    def runGOLRuleOnBoard(self, gameOfLifeRules, playerIds):
        # Get copy of old board
        oldBoard = [row[:] for row in self.boardPlayerIds]
        # Calculate new state of board
        newBoard = self.getClearBoard()
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                # Count neighbors
                numNeighbors = self.countNeighbors(oldBoard, x, y)
                if oldBoard[x][y]['playerId'] == None:
                    # Cell was dead. Birth time?
                    if numNeighbors in gameOfLifeRules['b']:
                        newBoard[x][y] = {"playerId":random.choice(playerIds),"age":0}
                    else:
                        # Cell remains dead
                        newBoard[x][y] = dict(oldBoard[x][y])
                        newBoard[x][y]['age'] += 1
                if oldBoard[x][y]['playerId'] != None:
                    # Cell was alive. Stays alive?
                    if numNeighbors in gameOfLifeRules['s']:
                        newBoard[x][y] = dict(oldBoard[x][y]) # copy dict
                        newBoard[x][y]['age'] += 1
                    else:
                        # Cell dies of loneliness
                        newBoard[x][y] = dict(oldBoard[x][y])
                        newBoard[x][y]['age'] = 0
                        newBoard[x][y]['playerId'] = None
        # Annotate board with old playerId on each cell
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                newBoard[x][y]['lastPlayerId'] = oldBoard[x][y]['playerId']

        print(f'Board at frame {self.currFrame}')
        #self.printBoardToConsole(newBoard)

        self.boardPlayerIds = newBoard

    def printBoardToConsole(self, boardArray):
        for y in range(self.boardHeight):
            print (''.join(['*' if (boardArray[x][y]['playerId'] != None) else ' ' for x in range(self.boardWidth)]))
            #print ([str(self.countNeighbors(boardArray, x, y)) for x in range(self.boardWidth)])

    def setCell(self, x, y, playerId):
        self.boardPlayerIds[x][y]['playerId'] = playerId

    def nextFrame(self, playerIds):
        self.currFrame += 1
        self.runGOLRuleOnBoard(self.gameOfLifeRules, playerIds)
    
@dataclass
class Player:
    playerId: str
    addCellCooldownEndTime: datetime = None

@dataclass
class Session:
    ws: WebSocket
    player: Player

sessions: list[Session] = []
board: Board = Board()
shutdownSignal: bool = False
timePerFrameMs = 1000
numFramesPerGame = 55

def getPlayers():
    return [s.player for s in sessions] + [Player(playerId="ghost")]

def resetBoard():
    global board
    board = Board()
    board.generateTestFrame([p.playerId for p in getPlayers()])
    broadcastMessage("board", getBoardUpdateData())

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
    broadcastMessage('playerList', {'players':[p.playerId for p in getPlayers()]})

def getBoardUpdateData():
    boardData = board.getBoardSendData()
    boardData['board']['nextRoundTime'] = (datetime.utcnow() + timedelta(milliseconds=timePerFrameMs)).replace(tzinfo=timezone.utc).isoformat()
    return boardData

async def runGameLoop():
    global board
    while not shutdownSignal:
        board.nextFrame([p.playerId for p in getPlayers()])
        broadcastMessage('board', getBoardUpdateData())
        if board.currFrame > numFramesPerGame:
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
        await websocket.send_json({"type":"yourPlayerInfo", "playerId":playerId})
        broadcastPlayersList()
        msg = getBoardUpdateData()
        msg['type'] = "board"
        await websocket.send_json(msg)
        while True:
            msg = await websocket.receive_json()
            msgType = msg['type']
            if msgType == 'addCell':
                print(msg)
                # Add cell to board
                board.setCell(msg['x'], msg['y'], thisSession.playerId)
                broadcastMessage('board', getBoardUpdateData())
                # Announce cooldown for clicking to client
                player.addCellCooldownEndTime = datetime.utcnow()+timedelta(seconds=10)
                await websocket.send_json({"type":"cooldownUpdate", "cooldownEndTime":player.addCellCooldownEndTime.replace(tzinfo=timezone.utc).isoformat()})
    finally:
        sessions.remove(thisSession)
        broadcastPlayersList()
    
