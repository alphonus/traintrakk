const state = @import("state.zig");
const std = @import("std");
const Vec2 = @import("raylib").Vector2;
const expect = std.testing.expect;

const EntityType = enum {
    var count: u32 = 0;
    track,
    signal,
    balise, //technically a sensor
    sensor,
    train,
    cursor,
};

const TrainStatus = enum { Ready, Moving, Stopped };
const PathMode = enum(u2) {
    Linear,
    BSpline,
};
pub const Train = struct {
    const ent_type = EntityType.train;
    id: u32,
    direction: i2, //1 if with the track segment length; -1 if against
    status: TrainStatus,
    cur_track_id: u16,
    cur_track: *Track,
    cur_pos: f32,
    speed: u8,
    pub fn init(trac_ptr: *Track) Train {
        //const trac_ptr = Track.get_ptr(track_id);
        const track_id = trac_ptr.id;
        return Train{ .id = track_id, .direction = -1, .status = TrainStatus.Ready, .cur_track_id = 0, .cur_track = trac_ptr, .cur_pos = 0.1, .speed = 0 };
    }
};

pub const Point = struct {
    const tol = 5.0;
    x: u32,
    y: u32,
    fn vector(self: Point, other: Point) [2]f32 {
        const x_comp: f32 = @as(f32, @floatFromInt(other.x)) - @as(f32, @floatFromInt(self.x));
        const y_comp: f32 = @as(f32, @floatFromInt(other.y)) - @as(f32, @floatFromInt(self.y));
        return .{ x_comp, y_comp };
    }
    pub fn dist(self: Point, other: Point) f32 {
        //try std.debug.print("Train with ID: {s} does not exist!\n", .{@typeInfo(self)});
        const x_comp, const y_comp = Point.vector(self, other);
        return @sqrt(x_comp * x_comp + y_comp * y_comp);
    }
    fn snap(self: *Point, other: Point) bool {
        return (self.dist(other) <= .tol);
    }
    fn get_nn() void {
        unreachable;
    }
};
const Sensor = struct {
    const ent_type = EntityType.sensor;
    point: Vec2,
};

pub const Track = struct {
    const ent_type = EntityType.track;
    start: Vec2,
    end: Vec2,
    id: u16,
    length: f32, //in cm
    next: ?*Track, //only allow non switched at current implementation!!!NEDS TO BE IDS
    prev: ?*Track, //only allow non switched at current implementation
    fn new_segment(self: *Track, pos: f32) ?Track {
        if (pos > self.length) {
            return self.next;
        } else {
            if (pos < 0.0) {
                return self.prev;
            } else {
                return null;
            }
        }
    }

    pub fn get_track_pos_render(self: *Track, position: f32) Vec2 {
        //return Vec2.add(self.start, Vec2.scale(Vec2.subtract(self.end, self.start), position));
        return Vec2.lerp(self.start, self.end, position);
    }
    fn oob(self: *Track, pos: f32) bool {
        return (pos > self.length or pos < 0.0);
    }
    fn checkin(self: *Track, track_id: u32) .{ f32, i2 } {
        //sets new position and travel direction of entering train
        //assumes the tracks are connected, no error handeling
        switch (track_id) {
            self.prev.id => return .{ 0.0, 1 },
            self.next.id => return .{ 1.0, -1 },
            else => unreachable,
        }
    }
    pub fn init(start: Vec2, end: Vec2, prev: ?*Track, next: ?*Track) Track {
        const dist = Vec2.distance(start, end);
        //connections to be done later
        const id = 1;
        return Track{ .start = start, .end = end, .id = id, .length = dist, .prev = prev, .next = next };
    }
};

pub const MMR = struct {
    TrackList: std.ArrayList(Track),
    TrainList: std.ArrayList(Train),
    SensorList: std.ArrayList(Sensor),
    //track_registry: std.AutoHashMap(u32, Track),
    //train_registry: std.AutoHashMap(u32, Train),
    //sensor_registry: std.AutoHashMap(u32, Sensor),

    pub fn add_track_segment(self: *MMR, segment: Track) !void {
        try self.TrackList.append(segment);
    }

    pub fn add_sensor(self: *MMR, sensor: Sensor) !void {
        try self.SensorList.append(sensor);
    }
    pub fn add_train(self: *MMR, train: Train) !void {
        try self.TrainList.append(train);
    }
};

pub fn init_mmr(allocator: std.mem.Allocator) MMR {
    var TrackList = std.ArrayList(Track).init(allocator);
    defer TrackList.deinit();
    var Sensors = std.ArrayList(Sensor).init(allocator);
    defer Sensors.deinit();
    var Trains = std.ArrayList(Train).init(allocator);
    defer Trains.deinit();
    return MMR{
        .TrackList = TrackList,
        .SensorList = Sensors,
        .TrainList = Trains,
    };
}
const TIME_DELTA = 0.5;
fn update_train_pos(model: *MMR, train_id: u32) void {
    //var t_id ;
    const maybe_train_index = for (model.TrainList.items, 0..) |t, i| {
        if (t.id == train_id) {
            break i;
        } else null;
    };
    if (maybe_train_index) |train_index| {
        const train_ptr = &model.TrainList[train_index];
        if (train_ptr.status != TrainStatus.Moving) {
            try std.debug.print("Train with ID: {d} is shut off.\n", .{train_id});
            return;
        }
        const distance = train_ptr.speed() * TIME_DELTA;
        const track_ptr: *Track = @fieldParentPtr("cur_track_id", train_ptr.cur_track_id);
        const next_segment = track_ptr.new_segment(train_ptr.cur_pos + distance);
        if (next_segment) |n_track| {
            // Simple transition to next track
            const next_id = n_track.id;
            _ = next_id;
            const new_pos, const mov_dir = n_track.checkin(track_ptr.id);
            train_ptr.direction = mov_dir;
            train_ptr.cur_pos = new_pos;
        } else {
            // train not moving to new track
            if (track_ptr.oob(train_ptr.cur_pos + distance)) {
                train_ptr.status = TrainStatus.Stopped;
                train_ptr.cur_pos = if (train_ptr.mov_dir == 1) 1.0 else 0.0;
            } else {
                train_ptr.cur_pos += distance;
            }
        }
    } else {
        try std.debug.print("Train with ID: {d} does not exist!\n", .{train_id});
    }
}

const TrackEntities = union(EntityType) {
    track: Track,
    signal: Sensor,
    sensor: Sensor,
    balise: Sensor,
    train: Train
}