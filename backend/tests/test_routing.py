from app.services.routing import GeoPoint, best_path, build_distance_matrix, two_opt


def test_haversine_matrix_is_symmetric():
    pts = [
        GeoPoint("a", 43.07, -89.41),
        GeoPoint("b", 43.08, -89.39),
        GeoPoint("c", 43.05, -89.42),
    ]
    m = build_distance_matrix(pts)
    for i in range(3):
        for j in range(3):
            assert abs(m[i][j] - m[j][i]) < 1e-9
        assert m[i][i] == 0


def test_two_opt_does_not_increase_path_length():
    pts = [
        GeoPoint("a", 0, 0),
        GeoPoint("b", 0, 10),
        GeoPoint("c", 10, 10),
        GeoPoint("d", 10, 0),
        GeoPoint("e", 5, 5),
    ]
    dm = build_distance_matrix(pts)
    initial = list(range(len(pts)))

    def length(order):
        return sum(dm[order[i]][order[(i + 1) % len(order)]] for i in range(len(order)))

    before = length(initial)
    after = length(two_opt(initial.copy(), dm))
    assert after <= before + 1e-9


def test_best_path_closes_loop_with_anchor_first_and_last():
    pts = [
        GeoPoint("anchor", 43.07, -89.41),
        GeoPoint("b", 43.08, -89.39),
        GeoPoint("c", 43.05, -89.42),
        GeoPoint("d", 43.10, -89.40),
    ]
    ordered = best_path(pts)
    assert ordered[0] == "anchor"
    assert ordered[-1] == "anchor"
    assert set(ordered) == {"anchor", "b", "c", "d"}
