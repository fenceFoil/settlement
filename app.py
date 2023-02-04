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

    def __init__(self):
        self.boardPlayerIds = [[None for x in range(self.boardHeight)] for y in range(self.boardHeight)]

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

    def nextFrame(self):
        return self.generateTestFrame()
    
    
sessions: list[WebSocket] = []
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
    sessions.append(websocket)
    print("Session connected")
    try:
        msg = getBoardUpdateData()
        msg['type'] = "board"
        await websocket.send_json(msg)
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    finally:
        sessions.remove(websocket)
    
