from fastapi import FastAPI


DATABASE = 'sqlite:///sqlite.db'

app = FastAPI(title="REST API using FastAPI sqlite Async endpoits")
