const rl = @import("raylib");
const std = @import("std");
const test_allocator = std.testing.allocator;
const grid_step = 20;


const Path_List = struct {
    list: std.ArrayList(.{u32, u32}),
};
const State = struct {};
fn get_nn(mousepos: rl.Vector2) @Vector(2, u32) {
    //Returns the position of the nearest center.
    //const width = rl.getScreenWidth();
    //const height = rl.getScreenHeight();
    const c_w: i32 = @intFromFloat(mousepos.x);
    const c_h: i32 = @intFromFloat(mousepos.y);
    const lowerbound_w = grid_step * @divFloor(c_w, grid_step);
    const mod_w = @mod(c_w, grid_step);
    const lowerbound_h = grid_step * @divFloor(c_h, grid_step);
    const mod_h = @mod(c_h, grid_step);
    const x = if (mod_w < grid_step / 2) lowerbound_w else lowerbound_w + grid_step;
    const y = if (mod_h < grid_step / 2) lowerbound_h else lowerbound_h + grid_step;
    return .{ x, y };
}

fn interpolate_path(start: @Vector(2, i32), end: @Vector(2, i32)) [3]@Vector(2, i32) {
    //create constraine path to fit direct line between points to grid.
    const path = end - start;
    if (std.math.absInt(path[0]) > std.math.absInt(path[1])) {
        //x component larger
        const x_travel = path[0] - path[1];
        return [_]@Vector(2, i32){ start, @Vector(2, i32){ start[0] + x_travel, start[1] }, end };
    } else {
        //y component larger
        const y_travel = path[1] - path[0];
        return [_]@Vector(2, i32){ start, @Vector(2, i32){ start[0], start[1] + y_travel }, end };
    }
}

fn draw_grid() void {
    const width = rl.getScreenWidth();
    const height = rl.getScreenHeight();
    var w: i32 = 10;
    var h: i32 = 10;
    while (w < width) : (w += grid_step) {
        rl.drawLine(w, 0, w, height, .black);
    }
    while (h < height) : (h += grid_step) {
        rl.drawLine(0, h, width, h, .black);
    }
}

const SplineNode = struct {
    x: i32,
    y: i32,
    i: f32,
    fn init(x: i32, y: 32) SplineNode {
        return SplineNode{ .x = x, .y = y };
    }

    fn dist(self: SplineNode, pos: rl.Vector2) f32 {
        return @sqrt(std.math.pow(f32, (pos.x - @as(f32, @floatFromInt(self.x))), 2) + std.math.pow(f32, (pos.y - @as(f32, @floatFromInt(self.y))), 2));
    }
};
const SplineMode = enum{Iso};
const Spline = struct {
    nodes: [3]rl.Vector2,//[3]@Vector(2, u16),
    nnodes: i8 = 0,
    smooth_grade: u8 = 1,
    //polynomials: @vector(3-1,[_]f32),
    next: *Spline,
    prev: *Spline,
    switches: [*]Spline,
    //mode: SplineMode = Iso,
    
    fn interp_lin(u:f16) rl.Vector2 {
        const segment =  @intFromFloat(u);
        const t_u = u - segment;
        return t_u*nodes[segment+1]-(1-t_u)*nodes[segment];
    }

    fn f(t:f16, mode:?SplineMode) rl.Vector2 {

        if (mode == null){
            mode = Iso;
        }
        switch (mode) {
            Iso => return interp_lin(t*nodes.len),
        }
    }
    fn init(point: rl.Vector2) Spline {
        nodes[0] = point;
        nnodes += 1;
    }

    fn add(point: rl.Vector2) void {
        if (point==nodes[0]) {
            // prevent rendering and calculation if nodes too close
            return;
        }
        const components = point - nodes[0];
        switch (mode) {
            Iso => {
                if (@fabs(components[0]) < @fabs(components[1])) {
                    //asume slope of 1 for interpolated point
                    const P2 = rl.Vector2{nodes[0][0],nodes[0][1]+components[1]-components[0]};
                } else {
                    //dx > dy
                    const P2 = rl.Vector2{nodes[0][0]+components[0]-components[1],nodes[0][1]}; 
                }
                nodes[1] = P2;
                nodes[2] = point;
                nnodes += 2;
            }
        }
    } 

    fn render() void {
        rl.drawSplineLinear(nodes, 0.1, .black);
    }
}

pub fn main() !void {
    const screenWidth = 800;
    const screenHeight = 450;

    rl.initWindow(screenWidth, screenHeight, "Tesdt Window");
    //rl.showCursor();
    rl.setTargetFPS(30);
    defer rl.closeWindow();
    var mousepos: rl.Vector2 = rl.Vector2.zero();
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var nodes = std.ArrayList(rl.Vector2).init(allocator);
    defer nodes.deinit();
    var node_focused: i32 = -1;
    var node_selected: i32 = -1;
    var cursor: @Vector(2, u32);// = get_nn(mousepos);
    while (!rl.windowShouldClose()) {
        mousepos = rl.getMousePosition();
        cursor = get_nn(mousepos);

        //check if cursor close to a node
        blk: {
            for (nodes.items, 0..nodes.items.len) |item, k| {
                if (item.dist(mousepos) < 10.0) {
                    node_focused = k;
                    if (rl.isMouseButtonReleased(.left)) {
                        node_selected = node_focused;
                    }
                    break :blk;
                }
            }
            node_focused = -1;
        }
        if (rl.isMouseButtonReleased(.left) and node_focused == -1) {
            if (node_selected > -1) {
                //get associated spline

                //push to spline
                spline.add(cursor);
            } else {
                //start new spline/node
                nodes.append(cursor);
            }
        }
        rl.beginDrawing();
        defer rl.endDrawing();
        rl.clearBackground(.ray_white);
        draw_grid();

        rl.drawText("test", 10, 10, 30, .black);

        rl.drawCircle(cursor[0], cursor[1], 10, .green);

        if (rl.isMouseButtonReleased(.left)) {
            var i: usize = 0;
            var found = false;
            for (nodes.items, 0..nodes.items.len) |item, k| {
                if (!found and item.dist(mousepos) < 10.0) {
                    i = k;
                    found = true;
                }
            }
            if (found)
            //check if in area of circle
            //remove circle
            {
                _ = nodes.swapRemove(i);
            }
            //add new circle
            else {
                //intpos = .{@intFromFloat(mousepos.x), @intFromFloat(mousepos.y)};
                try nodes.append(.{ .x = @intFromFloat(mousepos.x), .y = @intFromFloat(mousepos.y) });
            }
            std.debug.print("width:{d}, rednerwidth:{d}\n", .{ rl.getScreenWidth(), rl.getRenderWidth() });
            std.debug.print("Cursor x:{d}, y:{d}\n", .{ mousepos.x, mousepos.y });
            std.debug.print("len{d}\n", .{nodes.items.len});
        }
        for (nodes.items) |item| {
            rl.drawCircle(item.x, item.y, 10, .red);
        }
    }
}
