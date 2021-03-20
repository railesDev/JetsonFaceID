from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://usr:pass@localhost:5432/sqlalchemy')
Session0 = sessionmaker(bind=engine)
Session = Session0()
Session._model_changes = {}
Base = declarative_base()

# create_engine('postgresql://postgres:{pw}@localhost:5432/scrape'.format(pw=POSTGRES_PASSWORD))

