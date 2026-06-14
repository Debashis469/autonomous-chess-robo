#pragma once
#include <cstdint>

using U64 = uint64_t;

inline int popcount(U64 bb) {
  return __builtin_popcountll(bb);
}

inline int lsb(U64 bb) {
  return __builtin_ctzll(bb);
}

inline void pop_bit(U64& bb) {
  bb &= bb - 1;
}