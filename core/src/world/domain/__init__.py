class DomainObject:
    item_type = NotImplementedError

    def serialize(self):
        raise NotImplementedError
