# SC REFINERY API HTTP REFERENCE

## User

### Get User

Requires user perm ``user.read``

```
GET /user/{id} HTTP/1.1 
```

### List Users

Requires user perm ``user.index``

Supports query parameters:

* ``sort`` - list of columns with direction in the form of ``col1:asc|desc[;col2:asc|desc]``
* ``filter`` - list of columns with search terms in the form of ``col1:term[;col2:term]``
* ``offset`` - number of rows to skip
* ``limit`` - number of results to return

```
GET /user/{?sort,filter,offset,limit} HTTP/1.1 
```

### Create User

Requires user perm ``user.create``

```
POST /user/ HTTP/1.1 
Content-Type: application/json

{
    "mail": "user@domain.tld",
    "password": "user password",
    "password_confirm": "user password repeated for confirmation",
    "perms": ["array", "with", "strings"]
}
```

### Update User

Requires user perm ``user.update``

```
PUT /user/{id} HTTP/1.1 
Content-Type: application/json

{
    "mail": "user@domain.tld",
    "password": "user password",
    "password_confirm": "user password repeated for confirmation",
    "perms": ["array", "with", "strings"]
}
```

### Remove User

Requires user perm ``user.remove``

```
DELETE /user/{id} HTTP/1.1 
```


## Ore

### Get Ore

Requires user perm ``ore.read``

```
GET /ore/{id} HTTP/1.1 
```

### List Ores

Requires user perm ``ore.index``

Supports query parameters:

* ``sort`` - list of columns with direction in the form of ``col1:asc|desc[;col2:asc|desc]``
* ``filter`` - list of columns with search terms in the form of ``col1:term[;col2:term]``
* ``offset`` - number of rows to skip
* ``limit`` - number of results to return

```
GET /ore/{?sort,filter,offset,limit} HTTP/1.1 
```

### Create Ore

Requires user perm ``ore.create``

```
POST /ore/ HTTP/1.1 
Content-Type: application/json

{
    "name": "Quantanium"
}
```

### Update Ore

Requires user perm ``ore.update``

```
PUT /ore/{id} HTTP/1.1 
Content-Type: application/json

{
    "name": "Quantanium"
}
```

### Remove Ore

Requires user perm ``ore.remove``

```
DELETE /ore/{id} HTTP/1.1 
```


## Station

### Get Station

Requires user perm ``station.read``

```
GET /station/{id} HTTP/1.1 
```

### List Stations

Requires user perm ``station.index``

Supports query parameters:

* ``sort`` - list of columns with direction in the form of ``col1:asc|desc[;col2:asc|desc]``
* ``filter`` - list of columns with search terms in the form of ``col1:term[;col2:term]``
* ``offset`` - number of rows to skip
* ``limit`` - number of results to return

```
GET /station/{?sort,filter,offset,limit} HTTP/1.1 
```

### Create Station

Requires user perm ``station.create``

```
POST /station/ HTTP/1.1 
Content-Type: application/json

{
    "name": "ARC L-1",
    "efficiency": [
        {"ore_id": 1, "efficiency_bonus": 0.1},
        {"ore_id": 2, "efficiency_bonus": 0.95}
    ]
}
```

### Update Station

Requires user perm ``station.update``.

Note that ``efficiency`` is always replaced.

```
PUT /station/{id} HTTP/1.1 
Content-Type: application/json

{
    "efficiency": [
        {"ore_id": 1, "efficiency_bonus": 0.1},
        {"ore_id": 2, "efficiency_bonus": 0.95},
        {"ore_id": 3, "efficiency_bonus": 0.2}
    ]
}
```

### Remove Station

Requires user perm ``station.remove``

```
DELETE /station/{id} HTTP/1.1 
```


## Method

### Get Method

Requires user perm ``method.read``

```
GET /method/{id} HTTP/1.1 
```

### List Methods

Requires user perm ``method.index``

Supports query parameters:

* ``sort`` - list of columns with direction in the form of ``col1:asc|desc[;col2:asc|desc]``
* ``filter`` - list of columns with search terms in the form of ``col1:term[;col2:term]``
* ``offset`` - number of rows to skip
* ``limit`` - number of results to return

```
GET /method/{?sort,filter,offset,limit} HTTP/1.1 
```

### Create Method

Requires user perm ``method.create``

```
POST /method/ HTTP/1.1 
Content-Type: application/json

{
    "name": "Dinyx Solventation",
    "ores": [
        {"ore_id": 1, "efficiency": 0.975, "cost": 10, "duration": 60},
        {"ore_id": 2, "efficiency": 0.95, "cost" 400, "duration": 10}
    ]
}
```

### Update Method

Requires user perm ``method.update``.

Note that ``ores`` is always replaced.

```
PUT /method/{id} HTTP/1.1 
Content-Type: application/json

{
    "ores": [
        {"ore_id": 1, "efficiency": 0.975, "cost": 10, "duration": 60},
        {"ore_id": 2, "efficiency": 0.95, "cost" 400, "duration": 10}
    ]
}
```

### Remove Method

Requires user perm ``method.remove``

```
DELETE /method/{id} HTTP/1.1 
```
