from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalogdb_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


user1 = User(name="Ahmed Assaf", email="AhmedAssaf1988@gmail.com")

session.add(user1)
session.commit()


user2 = User(name="Lujain Ghul", email="lujain.ghul@gmail.com")
session.add(user2)
session.commit()


# category
cat1 = Category(name="Soccer")

session.add(cat1)
session.commit()

item_1 = Item(name="Shingaurd", desc="""
The rules of association football were codified in England
by the Football Association in 1863 and the name association
football was coined to distinguish the game from the other
forms of football p
""", category=cat1, user=user1)
item_2 = Item(name="Players, equipment, and officials", desc="""
Each team consists of a maximum of eleven players
(excluding substitutes), one of whom must be the goalkeeper.
Competition rules may state a minimum number of players required
to constitute a team, which is usually seven
""", category=cat1, user=user1)
item_3 = Item(name="Ball", desc="""
The ball is spherical with a circumference of between 68 and 70
centimetres (27 and 28 in), a weight in the range of 410 to 450
grams (14 to 16 oz), and a pressure between 0.6 and 1.1 bars
(8.5 and 15.6 pounds per square inch) at sea level
""", category=cat1, user=user2)

session.add(item_1)
session.add(item_2)
session.add(item_3)
session.commit()


cat2 = Category(name="Snowboarding")
session.add(cat2)
session.commit()

item_4 = Item(name="Jibbing", desc="""
is technical riding on non-standard surfaces,
which usually includes performing tricks
. The word  jib is both a noun and a verb, depending on the usage of the word
. As a noun: a jib includes metal rails,
boxes, benches, concrete ledges, walls,
vehicles,rocks and logs
""", category=cat2, user=user2)

item_5 = Item(name="Freestyle", desc="""
Freestyle snowboarding is any riding that includes performing tricks.
In freestyle, the rider utilizes natural and man-made features such as rails,
jumps, boxes, and innumerable others to perform tricks. It is a popular
all-inclusive concept that distinguishes the creative aspects of snowboarding,
in contrast to a style like alpine snowboarding.
""", category=cat2, user=user1)

item_6 = Item(name="Freeriding", desc="""
Freeriding communicates the concept of dynamically
altering various snowboarding
styles in a fluid motion, allowing for a spontaneous ride on naturally
rugged terrain
""", category=cat2, user=user1)

session.add(item_4)
session.add(item_5)
session.add(item_6)
session.commit()

cat3 = Category(name="Basketball")
session.add(cat3)
session.commit()

item_7 = Item(name="Positions", desc="""
Basketball positions in the offensive zone Although the rules do not
specify any positions whatsoever, they have evolved as part of basketball.
During the early years of basketball's evolution, two guards, two forwards,
and one center were used. In more recent times specific positions evolved,
but the current trend, advocated by many top coaches including
Mike Krzyzewski is towards positionless basketball
""", category=cat3, user=user1)

item_8 = Item(name="Strategy", desc="""
There are two main defensive strategies: zone defense and man-to-man defense.
In a zone defense, each player is assigned to guard a specific area
of the court. Zone defenses often allow the defense to double team the ball,
a manoeuver known as a trap.
In a man-to-man defense, each defensive player guards a specific opponent.
""", category=cat3, user=user1)

item_9 = Item(name="Shooting", desc="""
Typically, a player faces the basket with both feet facing the basket.
A player will rest the ball on the fingertips of the dominant hand
(the shooting arm) slightly above the head, with the other hand
supporting the side of the ball
""", category=cat3, user=user1)


session.add(item_7)
session.add(item_8)
session.add(item_9)
session.commit()

print "added Category and items!"
