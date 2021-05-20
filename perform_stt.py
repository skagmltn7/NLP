import os
from glob import glob
import warnings

import librosa
import soundfile
import Levenshtein as Lev
import torchaudio
from torch import Tensor
import torch
import numpy as np

from STT import load_model, stt
from pprint import pprint as pp
from basefunction.FindUMethod import MakeTXTFile, MakeFile

warnings.filterwarnings('ignore')

os.environ["CUDA_VISIBLE_DEVICES"] = "2"

print("Model loading... ")
model, vocab = load_model()
print("Done")


def make_scripts(ids):
    for id in ids:
        if not os.path.exists(f'data/origin_audio/{id}.wav') or not os.path.exists(f'data/scripts/{id}.ko.vtt'):
            print(f"Make scripts about {id}")
            MakeFile(f'https://www.youtube.com/watch?v={id}')


def __split_with_value(y, sr, intervals):
    len_interval = len(intervals)
    signals = list()
    time_stamps = list()

    i = 0
    while i < len_interval - 1:
        wav = y[int(intervals[i]):int(intervals[i + 1])]
        signals.append(wav)
        time_stamps.append(int(intervals[i]) / sr)
        i += 1

    wav = y[int(intervals[i]):]
    signals.append(wav)
    time_stamps.append(int(intervals[i]) / sr)

    return signals, time_stamps


def list_stt(ids):
    true_label = list()
    youtube_label = list()
    our_label = list()

    for id in ids:
        print(id)
        audio_path = f'data/origin_audio/{id}.wav'
        true_script = open(f'data/true/{id}.txt').read().splitlines()
        length = len(true_script) - 1
        script = open(f'data/script/{id}.ko.vtt').read().splitlines()[4:]

        times = list()
        subscribe = list()
        for idx in range(0, len(script), 3):
            times.append(string_to_ms(script[idx]))
            subscribe.append(script[idx + 1])

        features, input_lengths, time_stamps = parse_audio(audio_path, times)

        sentences = list()

        for feature, input_length, time_stamp in zip(features, input_lengths, time_stamps):
            y_hats = model.recognize(feature.unsqueeze(0).to('cuda'), input_length)
            sentence = vocab.label_to_string(y_hats.cpu().detach().numpy())
            sentences.append(sentence[0])

        our_label.append(sentences)
        true_label.append(true_script)
        youtube_label.append(subscribe)

        break

    return true_label, youtube_label, our_label


def parse_audio(audio_path, times):
    signal, sr = librosa.load(audio_path, sr=16000)
    signals, time_stamps = __split_with_value(signal, sr, times)
    features = list()
    input_lengths = list()

    for signal in signals:
        feature = torchaudio.compliance.kaldi.fbank(
            waveform=Tensor(signal).unsqueeze(0),
            num_mel_bins=80,
            frame_length=20,
            frame_shift=10,
            window_type='hamming'
        ).transpose(0, 1).numpy()

        feature -= feature.mean()
        feature /= np.std(feature)

        feature = torch.FloatTensor(feature).transpose(0, 1)

        features.append(feature)
        input_lengths.append(torch.LongTensor([len(feature)]))

    return features, input_lengths, time_stamps


def string_to_ms(string: str):
    times = string.split(':')
    hour, minute, second = int(times[0]), int(times[1]), float(times[2])

    return hour * 60 * 60 * 16000 + minute * 60 * 16000 + second * 16000


def char_distance(ref, hyp):
    ref = ref.replace(' ', '')
    hyp = hyp.replace(' ', '')

    dist = Lev.distance(hyp, ref)
    length = len(ref.replace(' ', ''))

    return dist, length


def calculate_CER(y, y_hat):
    total_dist = 0
    total_length = 0
    for ref, hyp in zip(y, y_hat):
        dist, length = char_distance(ref, hyp)
        total_dist += dist
        total_length += length

    cer = float(total_dist / total_length) * 100
    return cer


if __name__ == "__main__":
    ids = [os.path.basename(x)[:-4] for x in glob('data/true/*')]

    # make_scripts(ids)
    true_label, youtube_label, our_label = list_stt(ids)

    for tl, yl, ol, id in zip(true_label, youtube_label, our_label, ids):
        youtube_cer = calculate_CER(tl, yl)
        our_cer = calculate_CER(tl, ol)
        print(f"{id} : {youtube_cer}% | {our_cer}% | {'WIN' if our_cer < youtube_cer else 'LOSE'}")

        for y, o in zip(yl, ol):
            print(y)
            print(o)
            print('======')
