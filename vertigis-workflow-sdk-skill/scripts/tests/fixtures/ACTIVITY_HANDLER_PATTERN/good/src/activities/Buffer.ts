import type { IActivityHandler } from "@vertigis/workflow";

interface BufferInputs { units?: "meters" | "feet"; distance: number }
interface BufferOutputs { result: number }

export default class BufferActivity implements IActivityHandler {
    execute(inputs: BufferInputs): BufferOutputs {
        try {
            return { result: inputs.distance };
        } catch (error) {
            throw error;
        }
    }
}
