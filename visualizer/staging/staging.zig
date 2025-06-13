const Edge = struct {
    const Node = struct {
        x: u32,
        y: u32,
        type: NodeType,

        fn larger_component(self: *Node, other: *Node) .{ u32, u2 } {
            //returns the largest signed manhattan component and the axis of it
            const component_x = self.x - other.x;
            const component_y = self.y - other.y;
            if (@abs(component_x) >= @abs(component_y)) {
                return .{ component_x, 0 };
            } else {
                return .{ component_y, 1 };
            }
        }
    };
    //id: u16,
    start: .{ u32, u32 },
    end: .{ u32, u32 },
    fn parse_path_linear(start: Node, end: Node) [3]Node {
        _, const axis = start.larger_component(end);
        const component_x = end.x - start.x;
        const component_y = end.y - start.y;
        if (axis == 0) {
            const new_p_x: u32 = start.x + (-1) * (@abs(component_x) - @abs(component_y));
            const new_p_y = start.y;
            return [3]Node{ start, Node{ .x = new_p_x, .y = new_p_y }, end };
        } else {
            const new_p_x = start.x;
            const new_p_y: u32 = start.y + (-1) * (@abs(component_y) - @abs(component_x));
            return [3]Node{ start, Node{ .x = new_p_x, .y = new_p_y }, end };
        }
    }
    fn insert_path(path_members: [3]Node) void {
        for (1..path_members.len) |i| {
            Edges.append(Edge{ .start = path_members[i - 1], .end = path_members[i] });
        }
    }
    pub fn create(contrains: [2]Node, mode: PathMode) void {
        if (mode != PathMode.Linear) {
            unreachable; //future feature
        }
        const path_members = parse_path_linear(contrains[0], contrains[1]);
        insert_path(path_members);
    }
    fn check_equal(self: *Edge, other: *Edge) bool {
        return @eql(self, other) or (eql(self.start, other.end) and eql(self.end, other.start));
    }
};



fn insert_edge(path: Path, path_list: *std.ArrayList(Path)) state.InterfaceError!void {
    //insertion of a new edge+error checking, throw error if edge already present
    if (path_in(path, path_list)) {
        return error.Duplicate;
    }
    &path_list.append(path);
}
fn path_in(path: Path, path_list: *std.ArrayList(Path)) bool {
    return for (path_list.items) |new_path| {
        if (path.check_equal(new_path)) {
            break true;
        }
    } else false;
}
fn check_duplicate_path(path_list: std.ArrayList(Path)) ?[*]u32 {
    //returns the indexpositions of duplicate paths, null otherwise
    return null;
}

fn render_path(path_list: std.ArrayList(Path)) void {
    for (path_list.items) |path| {
        rl.drawSplineLinear(path, 0.1, .black);
    }
}