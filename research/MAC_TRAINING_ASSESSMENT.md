# Local hardware assessment — 24 September 2026

System inspection reports a MacBook Pro with Apple M5 (not M5 Pro), 10 CPU cores, 10 GPU cores, 16 GB unified memory, and macOS 26.2.

The existing pothole Python environment contains PyTorch 2.13.0 and Ultralytics 8.4.120. It was used read-only for a small diagnostic; no package or checkpoint was changed. Inside the restricted sandbox, PyTorch reported MPS unavailable. Repeating the diagnostic outside the sandbox reported:

```json
{
  "torch": "2.13.0",
  "mps_built": true,
  "mps_available": true,
  "gpu_forward_backward_ok": true
}
```

The diagnostic creates a 256×256 tensor on MPS, performs matrix operations and backpropagation, synchronizes the GPU, and checks that gradients are finite. It confirms access to basic GPU training operations. It is not a YOLO training benchmark and establishes no training-time or end-to-end throughput guarantee.

**Recommendation:** start the hackathon implementation and pretrained-model baseline on this Mac. A separate PC is not necessary to begin. Small-model fine-tuning is a reasonable next experiment if detector errors and labels justify it. Use a short measured run before committing to long training.

Conservative proposed starting settings: nano/small pretrained detector, 640-pixel training input, batch 1–2, no in-memory image cache, one experiment at a time. Increase only after observing actual memory use. The 16 GB pool is shared by the operating system, applications, CPU, and GPU; it is not equivalent to a GPU with 16 GB dedicated VRAM plus separate system RAM.

Training a large video model or a detector from scratch is not a sensible starting plan for this project on this configuration. Use a suitable NVIDIA machine if measured memory needs, training time, operator compatibility, or the deadline demand it. The user's PC GPU and VRAM have not been provided, so a hardware comparison is still unresolved.

Final offline compatibility and the three-times-duration budget must be validated on Linux/NVIDIA hardware representative of the organizers' T4-class machine. A successful Mac run does not prove that requirement. A local NVIDIA PC is one option; an already available remote GPU is another. No paid compute has been authorized or provisioned.

Primary documentation checked:

- [Ultralytics training: Apple Silicon MPS](https://docs.ultralytics.com/modes/train) — documents training with `device="mps"`.
- [Apple: accelerated PyTorch training on Mac](https://developer.apple.com/metal/pytorch/) — describes the MPS GPU backend and availability checks.
- [Apple: MacBook Pro with M5 specifications](https://support.apple.com/en-us/125405) — describes the chip and unified-memory configurations.

No model training was launched during this assessment.
