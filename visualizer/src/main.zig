const rl = @import("raylib");
const std = @import("std");

const grid_step = 20;

const logic = @import("logic.zig");

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

fn render_components(model: logic.MMR, train_texture: rl.Texture) void {
    //iterate through the model and render all compioents based on theri type

    //render track
    for (model.TrackList.items) |track| {
        //const start = rl.Vector2.init(@as(f32, @floatFromInt(track.start.x)), @as(f32, @floatFromInt(track.start.y)));
        //const end = rl.Vector2.init(@as(f32, @floatFromInt(track.end.x)), @as(f32, @floatFromInt(track.end.y)));
        rl.drawLineEx(track.start, track.end, 5.0, .red);
    }

    for (model.TrainList.items) |train| {
        const track = train.cur_track;
        const pos = track.get_track_pos_render(train.cur_pos);
        const x = @as(i32, @intFromFloat(pos.x));
        const y = @as(i32, @intFromFloat(pos.y));
        train_texture.draw(x, y, .white);
    }
}

pub fn main() !void {
    const screenWidth = 800;
    const screenHeight = 450;
    var gpa = std.heap.GeneralPurposeAllocator(.{}).init;
    const allocator = gpa.allocator();

    rl.initWindow(screenWidth, screenHeight, "Test Window");
    rl.setTargetFPS(30);
    defer rl.closeWindow();

    var model = logic.init_mmr(allocator);
    const p1 = rl.Vector2.init(20, 220);
    const p2 = rl.Vector2.init(140, 20);
    const p3 = rl.Vector2.init(120, 220);
    try model.add_track_segment(logic.Track.init(p1, p2, null, null));
    try model.add_track_segment(logic.Track.init(p3, p2, null, null));
    const t1 = logic.Train.init(&model.TrackList.items[0]);
    try model.add_train(t1);

    //const image = rl.Image.init("resources/train.png") catch |err| blk: {
    //    std.debug.print("Image Err: {}\n", .{err});
    //    break :blk rl.Image.genColor(30, 30, .green);
    //};

    //defer image.unload();
    const texture = try rl.Texture.init("resources/train.png");
    defer rl.unloadTexture(texture);

    while (!rl.windowShouldClose()) {
        const train = &model.TrainList.items[0];
        if (train.cur_pos > 1.0) {
            train.cur_pos = 0.0;
        } else {
            train.cur_pos += 0.05;
        }
        rl.beginDrawing();
        defer rl.endDrawing();

        rl.clearBackground(.ray_white);
        draw_grid();
        rl.drawText("test", 10, 10, 30, .black);
        render_components(model, texture);
    }
}
