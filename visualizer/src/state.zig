const InterfaceError = error{ Duplicate, Constraint, ObjectNotExist };
const GameError = InterfaceError || error{Oops};
