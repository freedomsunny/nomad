default = {
    "GET": ["admin", "service_ocmdb", "_member_", "user"],
    "POST": ["admin", "service_ocmdb", "_member_", "user"],
    "PUT": ["admin", "service_ocmdb", "_member_", "user"],
    "DELETE": ["admin", "service_ocmdb", "_member_", "user"],
}

policy = {
     "/helloworld$": {},
     "/physical/create$": {},
     "/physical/get$": {},
     "/physical/delete$": {},
     "/profile/get$": {},
     "/physical/finish$": {},
}
