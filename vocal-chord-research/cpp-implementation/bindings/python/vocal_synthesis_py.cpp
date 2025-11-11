#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "vocal_synthesis/aberration_params_v2.hpp"
#include "vocal_synthesis/audio_buffer.hpp"
#include "vocal_synthesis/dsp/glottal_incoherence.hpp"
#include "vocal_synthesis/dsp/subharmonic_generator.hpp"
#include "vocal_synthesis/dsp/pitch_stabilizer.hpp"
#include "vocal_synthesis/dsp/corporeal_noise.hpp"
#include "vocal_synthesis/dsp/subliminal_audio.hpp"

namespace py = pybind11;
using namespace vocal_synthesis;
using namespace vocal_synthesis::dsp;

PYBIND11_MODULE(vocal_synthesis, m) {
    m.doc() = "Vocal Synthesis Library - Real-time vocal tract aberration for character voices";

    // AudioBuffer
    py::class_<AudioBuffer>(m, "AudioBuffer")
        .def(py::init<>())
        .def(py::init<uint32_t, uint32_t>(), py::arg("sample_rate"), py::arg("num_channels") = 1)
        .def("resize", &AudioBuffer::resize)
        .def("clear", &AudioBuffer::clear)
        .def("size", &AudioBuffer::size)
        .def("num_frames", &AudioBuffer::numFrames)
        .def("sample_rate", &AudioBuffer::sampleRate)
        .def("num_channels", &AudioBuffer::numChannels)
        .def("peak", &AudioBuffer::peak)
        .def("rms", &AudioBuffer::rms)
        .def("rms_db", &AudioBuffer::rmsDB)
        .def("normalize", &AudioBuffer::normalize, py::arg("peak") = 0.8f)
        .def("apply_gain", &AudioBuffer::applyGain)
        .def("mix_from", &AudioBuffer::mixFrom, py::arg("other"), py::arg("gain") = 1.0f)
        .def("to_numpy", [](const AudioBuffer& buf) {
            return py::array_t<float>(buf.size(), buf.data());
        })
        .def("from_numpy", [](AudioBuffer& buf, py::array_t<float> arr) {
            py::buffer_info info = arr.request();
            buf.resize(info.shape[0]);
            std::memcpy(buf.data(), info.ptr, info.shape[0] * sizeof(float));
        });

    // AberrationParams
    py::class_<AberrationParams>(m, "AberrationParams")
        .def(py::init<>())
        .def_static("create_human", &AberrationParams::createHuman)
        .def_static("create_vampire", &AberrationParams::createVampire)
        .def_static("create_zombie", &AberrationParams::createZombie)
        .def_static("create_werewolf", &AberrationParams::createWerewolf)
        .def_static("create_wraith", &AberrationParams::createWraith)
        .def("describe", &AberrationParams::describe)
        .def("get_archetype", &AberrationParams::getArchetype);

    // Archetype enum
    py::enum_<AberrationParams::Archetype>(m, "Archetype")
        .value("HUMAN", AberrationParams::Archetype::HUMAN)
        .value("VAMPIRE", AberrationParams::Archetype::VAMPIRE)
        .value("ZOMBIE", AberrationParams::Archetype::ZOMBIE)
        .value("WEREWOLF", AberrationParams::Archetype::WEREWOLF)
        .value("WRAITH", AberrationParams::Archetype::WRAITH)
        .value("UNKNOWN", AberrationParams::Archetype::UNKNOWN);

    // EmotionState
    py::class_<EmotionState>(m, "EmotionState")
        .def(py::init<>())
        .def_static("from_named", &EmotionState::fromNamed)
        .def("apply_to", &EmotionState::applyTo);

    py::enum_<EmotionState::NamedEmotion>(m, "NamedEmotion")
        .value("NEUTRAL", EmotionState::NamedEmotion::NEUTRAL)
        .value("FEAR", EmotionState::NamedEmotion::FEAR)
        .value("ANGER", EmotionState::NamedEmotion::ANGER)
        .value("JOY", EmotionState::NamedEmotion::JOY)
        .value("SADNESS", EmotionState::NamedEmotion::SADNESS)
        .value("DISGUST", EmotionState::NamedEmotion::DISGUST);

    // GlottalIncoherence
    py::class_<GlottalIncoherence>(m, "GlottalIncoherence")
        .def(py::init<float, uint32_t>(), py::arg("sample_rate") = 48000.0f, py::arg("seed") = 42)
        .def("set_sample_rate", &GlottalIncoherence::setSampleRate)
        .def("set_intensity", &GlottalIncoherence::setIntensity)
        .def("set_dynamic_intensity", &GlottalIncoherence::setDynamicIntensity,
             py::arg("base_intensity"), py::arg("proximity"), py::arg("environment") = 0.5f)
        .def("set_components", &GlottalIncoherence::setComponents)
        .def("process_in_place", [](GlottalIncoherence& self, py::array_t<float> audio) {
            py::buffer_info buf = audio.request();
            self.processInPlace(static_cast<float*>(buf.ptr), buf.shape[0]);
        })
        .def("reset", &GlottalIncoherence::reset);

    // SubharmonicGenerator
    py::class_<SubharmonicGenerator>(m, "SubharmonicGenerator")
        .def(py::init<float>(), py::arg("sample_rate") = 48000.0f)
        .def("set_sample_rate", &SubharmonicGenerator::setSampleRate)
        .def("set_intensity", &SubharmonicGenerator::setIntensity)
        .def("set_chaos", &SubharmonicGenerator::setChaos)
        .def("set_transformation_struggle", &SubharmonicGenerator::setTransformationStruggle)
        .def("set_subharmonics", &SubharmonicGenerator::setSubharmonics)
        .def("process_in_place", [](SubharmonicGenerator& self, py::array_t<float> audio) {
            py::buffer_info buf = audio.request();
            self.processInPlace(static_cast<float*>(buf.ptr), buf.shape[0]);
        })
        .def("reset", &SubharmonicGenerator::reset);

    // SubliminalAudio
    py::class_<SubliminalAudio>(m, "SubliminalAudio")
        .def(py::init<float>(), py::arg("sample_rate") = 48000.0f)
        .def("set_sample_rate", &SubliminalAudio::setSampleRate)
        .def("set_layer", &SubliminalAudio::setLayer)
        .def("set_heartbeat_rate", &SubliminalAudio::setHeartbeatRate)
        .def("process_in_place", [](SubliminalAudio& self, py::array_t<float> audio) {
            py::buffer_info buf = audio.request();
            self.processInPlace(static_cast<float*>(buf.ptr), buf.shape[0]);
        })
        .def("reset", &SubliminalAudio::reset);

    py::enum_<SubliminalAudio::LayerType>(m, "SubliminalLayerType")
        .value("HEARTBEAT", SubliminalAudio::LayerType::HEARTBEAT)
        .value("BLOOD_FLOW", SubliminalAudio::LayerType::BLOOD_FLOW)
        .value("BREATH_CYCLE", SubliminalAudio::LayerType::BREATH_CYCLE)
        .value("ORGANIC_HUM", SubliminalAudio::LayerType::ORGANIC_HUM);
}

