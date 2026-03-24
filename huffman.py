import heapq
import os
import pickle
from collections import Counter




class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCoder:
    def __init__(self):
        self.codes = {}
        self.reverse_codes = {}

    def _build_tree(self, freqs):
        pq = [HuffmanNode(c, f) for c, f in freqs.items()]
        heapq.heapify(pq)
        if len(pq) == 1: # 处理只有一个字符的特殊情况
            node = heapq.heappop(pq)
            root = HuffmanNode(None, node.freq)
            root.left = node
            return root
        while len(pq) > 1:
            n1, n2 = heapq.heappop(pq), heapq.heappop(pq)
            merged = HuffmanNode(None, n1.freq + n2.freq)
            merged.left, merged.right = n1, n2
            heapq.heappush(pq, merged)
        return heapq.heappop(pq)

    def _generate_codes(self, root, current_code):
        if root is None: return
        if root.char is not None:
            self.codes[root.char] = current_code
            self.reverse_codes[current_code] = root.char
            return
        self._generate_codes(root.left, current_code + "0")
        self._generate_codes(root.right, current_code + "1")

    def compress(self, input_path):
        output_path = input_path + ".huff"
        # 字节流读取，支持所有文本编码
        with open(input_path, 'rb') as f:
            data = f.read()

        if not data: return None

        freqs = Counter(data)
        root = self._build_tree(freqs)
        self.codes = {}
        self._generate_codes(root, "")

        # 生成比特流字符串
        encoded_str = "".join([self.codes[b] for b in data])
        
        # 补齐逻辑：首字节存补零数
        extra_padding = 8 - len(encoded_str) % 8
        full_bit_str = "{0:08b}".format(extra_padding) + encoded_str + ("0" * extra_padding)
        
        # 转为字节数组写入
        byte_arr = bytearray()
        for i in range(0, len(full_bit_str), 8):
            byte_arr.append(int(full_bit_str[i:i+8], 2))

        with open(output_path, 'wb') as output:
            pickle.dump(freqs, output)
            output.write(byte_arr)
        
        return output_path

    def decompress(self, input_path):
        # 任务要求：输出为文本文件
        output_path = input_path.replace(".huff", "_decompressed.txt")

        with open(input_path, 'rb') as f:
            freqs = pickle.load(f)
            root = self._build_tree(freqs)
            self.reverse_codes = {}
            self._generate_codes(root, "")

            # 读取二进制数据并转为比特位
            bit_string = ""
            byte = f.read(1)
            while byte:
                # 关键：使用 byte[0] 直接获取整数值
                bit_string += format(byte[0], '08b')
                byte = f.read(1)

        extra_padding = int(bit_string[:8], 2)
        encoded_data = bit_string[8 : -extra_padding if extra_padding > 0 else None]

        # 译码为字节序列
        decoded_bytes = bytearray()
        curr = ""
        for bit in encoded_data:
            curr += bit
            if curr in self.reverse_codes:
                decoded_bytes.append(self.reverse_codes[curr])
                curr = ""

        # 任务要求：写回文本文件
        with open(output_path, 'wb') as output:
            output.write(decoded_bytes)
        
        return output_path