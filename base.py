from fastapi import FastAPI


DATABASE = 'sqlite:///sqlite1.db'

app = FastAPI(title="REST API using FastAPI sqlite Async endpoits")
