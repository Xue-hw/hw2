import heapq
import pickle
import os
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
        pq = [HuffmanNode(c, f) for c, f in freqs.items()]#构建优先队列
        heapq.heapify(pq)
        if len(pq) == 0: return None
        if len(pq) == 1:
            node = heapq.heappop(pq)
            root = HuffmanNode(None, node.freq)
            root.left = node
            return root
        # 合并节点
        while len(pq) > 1:
            n1, n2 = heapq.heappop(pq), heapq.heappop(pq)
            merged = HuffmanNode(None, n1.freq + n2.freq)
            merged.left, merged.right = n1, n2
            heapq.heappush(pq, merged)
        return heapq.heappop(pq)

    def _get_lengths(self, root, current_len, lengths):
        #获取字符对应的编码长度
        if root is None: return
        if root.char is not None:
            lengths[root.char] = current_len
            return
        self._get_lengths(root.left, current_len + 1, lengths)
        self._get_lengths(root.right, current_len + 1, lengths)

    def _generate_canonical_codes(self, lengths):
        # 根据长度生成范式哈夫曼编码
        if not lengths: return {}
        # 排序：先按长度，再按字符字典序
        sorted_items = sorted(lengths.items(), key=lambda x: (x[1], x[0]))
        
        codes = {}
        current_code = 0
        last_len = sorted_items[0][1]

        for char, length in sorted_items:
            current_code <<= (length - last_len)
            codes[char] = format(current_code, f'0{length}b')
            current_code += 1
            last_len = length
        return codes

    def compress(self, input_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_name = os.path.basename(input_path)
        # 将输出路径指向当前同级目录
        output_path = os.path.join(current_dir, base_name + ".huff")
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        if not text: return None

        #  统计字符频率并获取码长
        freqs = Counter(text)
        root = self._build_tree(freqs)
        lengths = {}
        self._get_lengths(root, 0, lengths)

        #  生成范式编码并转换数据
        self.codes = self._generate_canonical_codes(lengths)
        encoded_str = "".join([self.codes[c] for c in text])
        
        # 补齐位处理
        extra_padding = (8 - len(encoded_str) % 8) % 8
        full_bit_str = "{0:08b}".format(extra_padding) + encoded_str + ("0" * extra_padding)
        
        # 写入文件
        byte_arr = bytearray()
        for i in range(0, len(full_bit_str), 8):
            byte_arr.append(int(full_bit_str[i:i+8], 2))

        with open(output_path, 'wb') as output:
            pickle.dump(lengths, output) # 存储字符码长表
            output.write(byte_arr)
        return output_path

    def decompress(self, input_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_name = os.path.basename(input_path).replace(".huff", "_decompressed.txt")
        output_path = os.path.join(current_dir, base_name)
        with open(input_path, 'rb') as f:
            # 1. 加载码长表并重建范式映射
            lengths = pickle.load(f)
            self.codes = self._generate_canonical_codes(lengths)
            self.reverse_codes = {v: k for k, v in self.codes.items()}

            # 2. 读取二进制数据
            bit_string = ""
            chunk = f.read(1024*64) # 分块读取提高性能
            while chunk:
                bit_string += "".join(format(b, '08b') for b in chunk)
                chunk = f.read(1024*64)

        if not bit_string: return None
        extra_padding = int(bit_string[:8], 2)
        encoded_data = bit_string[8 : -extra_padding if extra_padding > 0 else None]

        # 3. 译码为字符串（注意：方案A处理的是字符）
        decoded_chars = []
        curr = ""
        for bit in encoded_data:
            curr += bit
            if curr in self.reverse_codes:
                decoded_chars.append(self.reverse_codes[curr])
                curr = ""

        # 4. 写回文本文件 (使用 utf-8 编码)
        with open(output_path, 'w', encoding='utf-8') as output:
            output.write("".join(decoded_chars))
        return output_path