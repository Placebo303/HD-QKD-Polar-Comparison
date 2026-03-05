#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr int kListSize = 4;

struct PathState {
    double pm = 0.0;
    std::vector<float> inter_llr;
    std::vector<uint8_t> inter_bits;
    std::vector<uint8_t> prev_state;
};

bool is_power_of_two(int x) {
    return x > 0 && (x & (x - 1)) == 0;
}

double f_node(double l, double r) {
    const double sl = (l >= 0.0) ? 1.0 : -1.0;
    const double sr = (r >= 0.0) ? 1.0 : -1.0;
    const double al = std::abs(l);
    const double ar = std::abs(r);
    return sl * sr * std::min(al, ar);
}

double g_node(double l, double r, int u) {
    return r - (2.0 * static_cast<double>(u) - 1.0) * l;
}

double pm_increment(double llr, int bit) {
    // Exact LLR-domain PM increment:
    // b=0 -> log(1+exp(-llr)); b=1 -> log(1+exp(llr))
    if (bit == 0) {
        if (llr >= 0.0) {
            return std::log1p(std::exp(-llr));
        }
        return -llr + std::log1p(std::exp(llr));
    }
    if (llr >= 0.0) {
        return llr + std::log1p(std::exp(-llr));
    }
    return std::log1p(std::exp(llr));
}

int check_crc16(const std::vector<uint8_t>& bits) {
    uint16_t reg = 0x0000;
    const uint16_t poly = 0x1021;
    for (size_t i = 0; i < bits.size(); i++) {
        const uint8_t top = static_cast<uint8_t>((reg >> 15) & 1U);
        reg = static_cast<uint16_t>((reg << 1) & 0xFFFFU);
        if (static_cast<uint8_t>(top ^ (bits[i] & 1U))) {
            reg ^= poly;
        }
    }
    return (reg == 0) ? 1 : 0;
}

void encoding_step_level(
    int level,
    int n_log,
    const uint8_t* source,
    uint8_t* result
) {
    const int pairs_per_group = 1 << (n_log - level - 1);
    const int step = pairs_per_group;
    const int groups = 1 << level;
    for (int g = 0; g < groups; ++g) {
        const int start = 2 * g * step;
        for (int p = 0; p < pairs_per_group; ++p) {
            result[start + p] = static_cast<uint8_t>(source[start + p] ^ source[start + p + step]);
            result[start + p + step] = source[start + p + step];
        }
    }
}

void compute_current_state(int pos, int n_log, std::vector<uint8_t>& state) {
    for (int b = 0; b < n_log; ++b) {
        const int shift = n_log - 1 - b;
        state[b] = static_cast<uint8_t>((pos >> shift) & 1);
    }
}

void update_alphas_for_pos(
    PathState& path,
    const std::vector<uint8_t>& current_state,
    int pos,
    int N,
    int n_log
) {
    for (int i = 1; i <= n_log; ++i) {
        if (current_state[i - 1] == path.prev_state[i - 1]) {
            continue;
        }
        const int src_len = N >> (i - 1);
        const int dst_len = src_len >> 1;
        const int src_off = (i - 1) * N;
        const int dst_off = i * N;

        if (current_state[i - 1] == 0) {
            for (int j = 0; j < dst_len; ++j) {
                const double l = path.inter_llr[src_off + j];
                const double r = path.inter_llr[src_off + j + dst_len];
                path.inter_llr[dst_off + j] = static_cast<float>(f_node(l, r));
            }
        } else {
            const int start = pos - dst_len;
            const int left_off = i * N + start;
            for (int j = 0; j < dst_len; ++j) {
                const double l = path.inter_llr[src_off + j];
                const double r = path.inter_llr[src_off + j + dst_len];
                const int u = static_cast<int>(path.inter_bits[left_off + j] & 1U);
                path.inter_llr[dst_off + j] = static_cast<float>(g_node(l, r, u));
            }
        }
    }
}

void commit_bit_and_propagate(
    PathState& path,
    const std::vector<uint8_t>& current_state,
    int pos,
    int bit,
    int N,
    int n_log
) {
    path.inter_bits[n_log * N + pos] = static_cast<uint8_t>(bit & 1);
    for (int level = n_log - 1; level >= 0; --level) {
        const int src_off = (level + 1) * N;
        const int dst_off = level * N;
        encoding_step_level(
            level,
            n_log,
            path.inter_bits.data() + src_off,
            path.inter_bits.data() + dst_off
        );
    }
    path.prev_state = current_state;
}

std::vector<uint8_t> decode_one_frame(
    const float* llr_ch,
    int N,
    int K,
    const std::vector<int>& info_idx,
    const std::vector<uint8_t>& info_mask,
    int n_log,
    bool debug_log
) {
    std::vector<PathState> paths;
    paths.reserve(kListSize);

    PathState init;
    init.pm = 0.0;
    init.inter_llr.assign(static_cast<size_t>((n_log + 1) * N), 0.0F);
    init.inter_bits.assign(static_cast<size_t>((n_log + 1) * N), 0U);
    init.prev_state.assign(static_cast<size_t>(n_log), 1U);
    for (int i = 0; i < N; ++i) {
        init.inter_llr[static_cast<size_t>(i)] = llr_ch[i];
    }
    paths.push_back(std::move(init));

    std::vector<uint8_t> current_state(static_cast<size_t>(n_log), 0U);

    for (int pos = 0; pos < N; ++pos) {
        compute_current_state(pos, n_log, current_state);
        const bool is_info = (info_mask[static_cast<size_t>(pos)] != 0U);

        if (!is_info) {
            for (auto& path : paths) {
                update_alphas_for_pos(path, current_state, pos, N, n_log);
                const double leaf_llr = static_cast<double>(path.inter_llr[static_cast<size_t>(n_log * N)]);
                path.pm += pm_increment(leaf_llr, 0);
                commit_bit_and_propagate(path, current_state, pos, 0, N, n_log);
            }
            continue;
        }

        std::vector<PathState> candidates;
        candidates.reserve(paths.size() * 2U);
        for (auto& base : paths) {
            update_alphas_for_pos(base, current_state, pos, N, n_log);
            const double leaf_llr = static_cast<double>(base.inter_llr[static_cast<size_t>(n_log * N)]);

            PathState child0 = base;
            child0.pm += pm_increment(leaf_llr, 0);
            commit_bit_and_propagate(child0, current_state, pos, 0, N, n_log);
            candidates.push_back(std::move(child0));

            PathState child1 = base;
            child1.pm += pm_increment(leaf_llr, 1);
            commit_bit_and_propagate(child1, current_state, pos, 1, N, n_log);
            candidates.push_back(std::move(child1));
        }

        std::sort(candidates.begin(), candidates.end(), [](const PathState& a, const PathState& b) {
            return a.pm < b.pm;
        });
        if (static_cast<int>(candidates.size()) > kListSize) {
            candidates.resize(static_cast<size_t>(kListSize));
        }
        paths = std::move(candidates);
    }

    int best_idx_any = -1;
    int best_idx_crc = -1;
    double best_pm_any = std::numeric_limits<double>::infinity();
    double best_pm_crc = std::numeric_limits<double>::infinity();

    for (int i = 0; i < static_cast<int>(paths.size()); ++i) {
        const auto& path = paths[static_cast<size_t>(i)];
        if (path.pm < best_pm_any) {
            best_pm_any = path.pm;
            best_idx_any = i;
        }

        std::vector<uint8_t> info_bits(static_cast<size_t>(K), 0U);
        for (int t = 0; t < K; ++t) {
            const int idx = info_idx[static_cast<size_t>(t)];
            info_bits[static_cast<size_t>(t)] = path.inter_bits[static_cast<size_t>(n_log * N + idx)];
        }
        if (check_crc16(info_bits) == 1) {
            if (path.pm < best_pm_crc) {
                best_pm_crc = path.pm;
                best_idx_crc = i;
            }
        }

        if (debug_log) {
            std::cout << "[C++] Path " << i << ": PM = " << path.pm
                      << ", CRC_Pass = " << (check_crc16(info_bits) == 1 ? 1 : 0)
                      << ", Decoded_Bits(first 20) = ";
            const int lim = std::min(20, K);
            for (int t = 0; t < lim; ++t) {
                if (t > 0) std::cout << ' ';
                std::cout << static_cast<int>(info_bits[static_cast<size_t>(t)] & 1U);
            }
            std::cout << "\n";
        }
    }

    const int final_idx = (best_idx_crc >= 0) ? best_idx_crc : best_idx_any;
    if (debug_log) {
        std::cout << "[C++] Selected Path = " << final_idx << "\n";
    }
    std::vector<uint8_t> out(static_cast<size_t>(K), 0U);
    if (final_idx < 0) {
        return out;
    }
    const auto& best = paths[static_cast<size_t>(final_idx)];
    for (int t = 0; t < K; ++t) {
        const int idx = info_idx[static_cast<size_t>(t)];
        out[static_cast<size_t>(t)] = static_cast<uint8_t>(best.inter_bits[static_cast<size_t>(n_log * N + idx)] & 1U);
    }
    return out;
}

template <typename T>
bool read_exact(std::ifstream& in, T* dst, size_t count) {
    in.read(reinterpret_cast<char*>(dst), static_cast<std::streamsize>(count * sizeof(T)));
    return static_cast<bool>(in);
}

bool write_bits_file(const std::string& out_path, const std::vector<uint8_t>& bits) {
    std::ofstream out(out_path, std::ios::binary);
    if (!out) {
        return false;
    }
    out.write(reinterpret_cast<const char*>(bits.data()), static_cast<std::streamsize>(bits.size()));
    return static_cast<bool>(out);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "Usage:\n";
        std::cerr << "  ca_scl <input_bin> <output_bin>\n";
        std::cerr << "input_bin layout:\n";
        std::cerr << "  int32 N, int32 K, int32 frames, uint8 mask[N], float llrs[frames*N]\n";
        return 2;
    }
    const std::string input_path = argv[1];
    const std::string out_path = argv[2];

    std::ifstream in(input_path, std::ios::binary);
    if (!in) {
        std::cerr << "Failed to open input file: " << input_path << "\n";
        return 3;
    }

    int32_t N_i32 = 0;
    int32_t K_i32 = 0;
    int32_t frames_i32 = 0;
    if (!read_exact(in, &N_i32, 1) || !read_exact(in, &K_i32, 1) || !read_exact(in, &frames_i32, 1)) {
        std::cerr << "Failed to read header (N,K,frames)\n";
        return 4;
    }
    const int N = static_cast<int>(N_i32);
    const int K = static_cast<int>(K_i32);
    const int frames = static_cast<int>(frames_i32);
    std::cout << "[C++] Received N=" << N << ", K=" << K << "\n";

    if (!is_power_of_two(N)) {
        std::cerr << "N must be power-of-two\n";
        return 5;
    }
    if (K <= 0 || K > N) {
        std::cerr << "K must satisfy 0 < K <= N\n";
        return 6;
    }
    if (frames <= 0) {
        std::cerr << "frames must be > 0\n";
        return 7;
    }
    const int n_log = static_cast<int>(std::round(std::log2(static_cast<double>(N))));
    if ((1 << n_log) != N) {
        std::cerr << "N power-of-two check failed\n";
        return 8;
    }

    std::vector<uint8_t> info_mask(static_cast<size_t>(N), 0U);
    if (!read_exact(in, info_mask.data(), static_cast<size_t>(N))) {
        std::cerr << "Failed to read mask\n";
        return 9;
    }
    std::vector<int> info_idx;
    info_idx.reserve(static_cast<size_t>(K));
    for (int pos = 0; pos < N; ++pos) {
        if ((info_mask[static_cast<size_t>(pos)] & 1U) != 0U) {
            info_idx.push_back(pos);
        }
    }
    if (static_cast<int>(info_idx.size()) != K) {
        std::cerr << "Mask ones count mismatch: expected K=" << K
                  << " got ones=" << static_cast<int>(info_idx.size()) << "\n";
        return 10;
    }
    std::cout << "[C++] Info Indices (mask=1): ";
    for (int i = 0; i < static_cast<int>(info_idx.size()); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << info_idx[static_cast<size_t>(i)];
    }
    std::cout << "\n";

    const size_t expected_llr_count = static_cast<size_t>(frames) * static_cast<size_t>(N);
    std::vector<float> llrs;
    llrs.resize(expected_llr_count);
    if (!read_exact(in, llrs.data(), expected_llr_count)) {
        std::cerr << "Failed reading llrs payload\n";
        return 11;
    }

    std::vector<uint8_t> out_bits(static_cast<size_t>(frames) * static_cast<size_t>(K), 0U);
    for (int f = 0; f < frames; ++f) {
        const float* frame_llr = llrs.data() + static_cast<size_t>(f) * static_cast<size_t>(N);
        const std::vector<uint8_t> decoded =
            decode_one_frame(frame_llr, N, K, info_idx, info_mask, n_log, f == 0);
        for (int t = 0; t < K; ++t) {
            out_bits[static_cast<size_t>(f) * static_cast<size_t>(K) + static_cast<size_t>(t)] =
                decoded[static_cast<size_t>(t)] & 1U;
        }
    }

    if (!write_bits_file(out_path, out_bits)) {
        std::cerr << "Failed writing output bits file: " << out_path << "\n";
        return 12;
    }

    return 0;
}
