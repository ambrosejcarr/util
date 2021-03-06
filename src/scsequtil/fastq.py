import numpy as np
from collections import namedtuple
from . import reader


class Record:
    """Abstract Fastq record object

    Defines several properties for accessing fastq record information:
    :property name: name field
    :property sequence: sequence field
    :property name2: second name field
    :property quality: quality field

    Also defines several methods for accessing SEQC annotation fields:
    :property annotations: list of annotations
    :property metadata: dictionary of read metadata (if any present)
    :property average_quality: return the mean quality of FastqRecord
    """

    __slots__ = ['_data', '_tags']

    def __init__(self, record):
        """

        :param [str|bytes] record: list of four strings or bytes objects containing a
          single fastq record
        """
        self._data = list(record)

    @property
    def name(self):
        return self._data[0]

    @name.setter
    def name(self, value):
        if not isinstance(value, (bytes, str)):
            raise TypeError('name must be str or bytes')
        else:
            self._data[0] = value

    @property
    def sequence(self):
        return self._data[1]

    @sequence.setter
    def sequence(self, value):
        if not isinstance(value, (bytes, str)):
            raise TypeError('sequence must be str or bytes')
        else:
            self._data[1] = value

    @property
    def name2(self):
        return self._data[2]

    @name2.setter
    def name2(self, value):
        if not isinstance(value, (bytes, str)):
            raise TypeError('name2 must be str or bytes')
        else:
            self._data[2] = value

    @property
    def quality(self):
        return self._data[3]

    @quality.setter
    def quality(self, value):
        if not isinstance(value, (bytes, str)):
            raise TypeError('quality must be str or bytes')
        else:
            self._data[3] = value

    def __bytes__(self):
        try:
            return b''.join(self._data)
        except TypeError:
            return ''.join(self._data).encode()

    def __str__(self):
        try:
            return ''.join(self._data)
        except TypeError:
            return b''.join(self._data).decode()

    def __repr__(self):
        return "Name: %s\nSequence: %s\nName2: %s\nQuality: %s\n" % (
            self._data[0], self._data[1], self._data[2], self._data[3])

    def __len__(self):
        return len(self.sequence)

    def average_quality(self):
        raise NotImplementedError

    def get_tags(self):
        raise NotImplementedError

    def get_tag(self, key):
        raise NotImplementedError

    def set_tag(self, key, value):
        raise NotImplementedError

    def set_tags(self, kv_pairs):
        raise NotImplementedError


class BytesRecord(Record):
    """Fastq record object

    Defines several properties for accessing fastq record information:
    :property bytes name: name field
    :property bytes sequence: sequence field
    :property bytes name2: second name field
    :property bytes quality: quality field

    Also defines several methods for accessing SEQC annotation fields:
    :property list annotations: list of annotations
    :property dict metadata: dictionary of read metadata (if any present)
    :property float average_quality: return the mean quality of FastqRecord
    """

    _bytes_itype_map = {
        b'i': int,
        b'Z': bytes,
        b'f': float}

    def get_tags(self):
        """
        :return list: annotations present in the fastq header
        """
        return {
            k.decode(): self._bytes_itype_map[t](v) for k, t, v in
            (v.split(b':') for v in self.name[1:].split(b';')[:-1])}

    def get_tag(self, key):
        try:
            return self.get_tags()[key]
        except KeyError:
            return None

    @staticmethod
    def _mktag(key, value):
        """internal method to create a bam-compatible tag from a key and value.

        construct a tag given a key, value pair
        :param str key:
        :param str | int | float | bytes value:
        :return bytes:
        """
        if type(value) is str:
            tag_type = b'Z'
            value = bytes(str(value), 'utf-8')
        elif type(value) is bytes:
            tag_type = b'Z'
        elif type(value) is float:
            tag_type = b'f'
            value = bytes(str(value), 'utf-8')
        elif type(value) is int:
            tag_type = b'i'
            value = bytes(str(value), 'utf-8')
        else:
            raise TypeError('tag type must be int, float, str, or bytes')

        return b'%b:%b:%b' % (
            key.encode(),
            tag_type,
            value)

    def set_tag(self, key, value):
        """prepends a tag to annotation name
        :param str key:
        :param str | int | float | bytes value:
        """
        self.name = b'@%s;%s' % (self._mktag(key, value), self.name[1:])

    def set_tags(self, kv_pairs):
        """prepend multiple tags to annotation name

        :param tuple((str, str | int | float | bytes),) kv_pairs: iterable of (key, value) tuples
        """
        self.name = b'@%s;%s' % (
            b';'.join(self._mktag(k, v) for k, v in kv_pairs),
            self.name[1:]
        )

    def average_quality(self):
        """"""
        return (
            np.mean(np.frombuffer(self.quality, dtype=np.int8, count=len(self)))
            .astype(int) - 33
        )


class StrRecord(Record):
    """Fastq record object

    Defines several properties for accessing fastq record information:
    :property str name: name field
    :property str sequence: sequence field
    :property str name2: second name field
    :property str quality: quality field

    Also defines several methods for accessing SEQC annotation fields:
    :property list annotations: list of annotations
    :property dict metadata: dictionary of read metadata (if any present)
    :property float average_quality: return the mean quality of FastqRecord
    """

    _str_itype_map = {
        'i': int,
        'Z': str,
        'f': float}

    def get_tags(self):
        """
        return all sequence tags.

        :return [(str, object)]: annotations present in the fastq header, type of value will depend
          upon the tag's type specific. Options: Int, string, float.
        """
        return {
            k: self._str_itype_map[t](v) for k, t, v in
            (v.split(':') for v in self.name[1:].split(';')[:-1])}

    def get_tag(self, key):
        try:
            return self.get_tags()[key]
        except KeyError:
            return None

    # todo should support bytes keys
    @staticmethod
    def _mktag(key, value):
        """
        construct a tag given a key, value pair

        :param str key:
        :param str | int | bytes | float value:
        :return str:
        """
        if type(value) is str:
            tag_type = 'Z'
        elif type(value) is float:
            tag_type = 'f'
            value = str(value)
        elif type(value) is int:
            tag_type = 'i'
            value = str(value)
        elif type(value) is bytes:
            tag_type = 'Z'
            value = value.encode()
        else:
            raise TypeError('tag type must be int, float, or str')

        return '%s:%s:%s' % (
            key,
            tag_type,
            value)

    def set_tag(self, key, value):
        """prepends a tag to annotation name

        :param str key: name of tag
        :param str | int | bytes | float value: value of tag
        """
        self.name = '@%s;%s' % (self._mktag(key, value), self.name[1:])

    def set_tags(self, kv_pairs):
        """prepend multiple tags to annotation name

        :param kv_pairs: Iterable of (key, value) tuples
        :return:
        """
        self.name = '@%s;%s' % (
            ';'.join(self._mktag(k, v) for k, v in kv_pairs),
            self.name[1:]
        )

    def average_quality(self):
        """calculate the average quality of the fastq read

        :return float: average quality of fastq read
        """
        return (
            np.mean(np.fromstring(self.quality, dtype=np.int8, count=len(self)))
            .astype(int) - 33
        )


class Reader(reader.Reader):
    """
    Fastq Reader, defines some special methods for reading and summarizing fastq data:

    :method __iter__: Iterator over fastq Record objects
    :method __len__: return number of records in file
    :method estimate_sequence_length: estimate the length of fastq sequences in file
    """

    @staticmethod
    def record_grouper(iterable):
        args = [iter(iterable)] * 4
        return zip(*args)

    def __iter__(self):
        record_type = StrRecord if self._mode == 'r' else BytesRecord
        for record in self.record_grouper(super().__iter__()):
            yield record_type(record)

    def estimate_sequence_length(self):
        """
        estimate the sequence length of a fastq file from the first 10000 records of
        the file.

        :return: int mean, float standard deviation, (np.ndarray: observed lengths,
          np.ndarray: counts per length)
        """
        i = 0
        records = iter(self)
        data = np.empty(10000, dtype=int)
        while i < 10000:
            try:
                seq = next(records).sequence
            except StopIteration:  # for fastq files shorter than 10000 records
                data = data[:i]
                break
            data[i] = len(seq) - 1  # last character is a newline
            i += 1
        return np.mean(data), np.std(data), np.unique(data, return_counts=True)


Tag = namedtuple('Tag', ['start', 'end', 'sequence_tag', 'quality_tag'])


class TagGenerator(Reader):

    def __init__(self, tags, *args, **kwargs):
        """parse fastq files for tag(s) defined by tag objects

        :param [Tag] tags: list of tag objects defining start and end of the sequence
          containing the tag, plus the string quality and sequence tags
        :param list|str files_: file or list of files to be read. Defaults to sys.stdin
        :param mode: open mode. Default 'r' will return string objects. Change to 'rb' to
          return bytes objects.
        """
        super().__init__(*args, **kwargs)
        self.tags = tags

    def __iter__(self):
        for record in super().__iter__():  # iterates fq records; we extract tags.
            tags = []
            for tag in self.tags:
                tags.extend(self.extract_tag(record, tag))
            yield tags

    @staticmethod
    def extract_tag(record, tag):
        seq = record.sequence[tag.start:tag.end]
        qual = record.quality[tag.start:tag.end]
        return (tag.sequence_tag, seq, 'Z'), (tag.quality_tag, qual, 'Z')
