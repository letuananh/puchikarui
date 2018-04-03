CREATE TABLE hobby (
       ID INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT
);

CREATE TABLE person_hobby (
       hid INTEGER,
       pid INTEGER,
      FOREIGN KEY (pid) REFERENCES person(ID) ON DELETE CASCADE ON UPDATE CASCADE,
      FOREIGN KEY (hid) REFERENCES hobby(ID) ON DELETE CASCADE ON UPDATE CASCADE
);