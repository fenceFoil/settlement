import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import random

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

boardPlayerIds = []

class Board:
    # 2 player
    boardPlayerIds:list[list[str]] = [[]]
    boardWidth:int = 8
    boardHeight:int = 8
    roundNumber:int = 0
    CONWAYS_GAME_OF_LIFE_RULES = {
        'b': [3],
        's': [2, 3]
    }
    gameOfLifeRules: dict = {
        'b': [3],
        's': [2, 3]
    }

    def getClearBoard(self):
        return [[None for x in range(self.boardHeight)] for y in range(self.boardHeight)]

    def __init__(self):
        self.boardPlayerIds = self.getClearBoard()

    def getBoardSendData(self):
        return {
            "board": {
                "roundNumber": self.roundNumber,
                "width": self.boardWidth,
                "height": self.boardHeight,
                "cells": self.boardPlayerIds
            }
        }

    def generateTestFrame(self):
        # Just shuffle them all lol
        self.roundNumber += 1
        self.boardPlayerIds = [
            [random.choice([{"playerId":None}, {"playerId":random.choice(["0", "1", "2"])}]) for x in range(self.boardHeight)]
            for y in range(self.boardHeight)]
        
    def countNeighbors(self, board, x, y):
        neighbors = 0
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            if x+dx > self.boardWidth:
                continue
            if x+dx < 0:
                continue
            if x+dx > self.boardWidth:
                continue
            if x+dx < 0:
                continue            
            neighbors += 1
        
    def runGOLRuleOnBoard(self, golRulesString):
        # Get copy of old board
        oldBoard = [row[:] for row in self.boardPlayerIds]
        # Calculate new state of board
        newBoard = self.getClearBoard()
        for x in range(self.boardWidth):
            for y in range(self.boardHeight):
                # Count neighbors
                int numNeighbors = countNeighbors(self, oldBoard, x, y)
                newBoard[x][y] = {"playerId":None}

        self.board = newBoard

    def nextFrame(self):
        return self.generateTestFrame()
    
class Session:
    ws: WebSocket
    playerId: str

sessions: list[Session] = []
board: Board = Board()
shutdownSignal: bool = False
timePerFrameMs = 2200

@app.on_event("startup")
async def setup():
    asyncio.create_task(runGameLoop())

def broadcastMessage(type:str, messageData):
    messageData['type'] = type
    for ws in sessions:
        async def doSendOneWSMsg():
            await ws.send_json(messageData)
        asyncio.create_task(doSendOneWSMsg())

def getBoardUpdateData():
    boardData = board.getBoardSendData()
    boardData['board']['nextRoundTime'] = (datetime.utcnow() + timedelta(milliseconds=timePerFrameMs)).replace(tzinfo=timezone.utc).isoformat()
    return boardData

async def runGameLoop():
    while not shutdownSignal:
        board.nextFrame()
        broadcastMessage("board", getBoardUpdateData())
        await asyncio.sleep(timePerFrameMs/1000.0)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    thisSession = Session(ws=websocket)
    sessions.append(thisSession)
    print("Session connected")
    try:
        thisSession.playerId = uuid.uuid4().urn
        await websocket.send_json({"type":"yourPlayerInfo", "playerId":thisSession.playerId})
        msg = getBoardUpdateData()
        msg['type'] = "board"
        await websocket.send_json(msg)
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    finally:
        sessions.remove(websocket)
    
