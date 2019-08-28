import os, inspect, time

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

PACK_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+"/.."

def makedir(path):
    try: os.mkdir(path)
    except: pass

def training(sess, neuralnet, saver, dataset, iteration, batch_size):

    start_time = time.time()
    loss_tr = 0
    list_loss = []
    list_psnr = []
    list_psnr_te = []

    makedir(PACK_PATH+"/training")
    makedir(PACK_PATH+"/static")
    makedir(PACK_PATH+"/static/bicubic")
    makedir(PACK_PATH+"/static/reconstruction")
    makedir(PACK_PATH+"/static/high-resolution")

    print("\nTraining SRCNN to %d iterations" %(iteration))
    train_writer = tf.compat.v1.summary.FileWriter(PACK_PATH+'/Checkpoint')
    for it in range(iteration):

        X_tr, Y_tr = dataset.next_batch(batch_size=batch_size, train=True)
        summaries, _ = sess.run([neuralnet.summaries, neuralnet.optimizer], feed_dict={neuralnet.inputs:X_tr, neuralnet.outputs:Y_tr})
        loss_tr, psnr_tr = sess.run([neuralnet.loss, neuralnet.psnr], feed_dict={neuralnet.inputs:X_tr, neuralnet.outputs:Y_tr})
        list_loss.append(loss_tr)
        list_psnr.append(psnr_tr)
        train_writer.add_summary(summaries, it)

        if(it % 100 == 0):
            np.save("loss", np.asarray(list_loss))

            randidx = int(np.random.randint(dataset.amount_tr, size=1))
            X_tr, Y_tr = dataset.next_batch(idx=randidx, train=True)

            img_recon, tmp_psnr = sess.run([neuralnet.recon, neuralnet.psnr], feed_dict={neuralnet.inputs:X_tr, neuralnet.outputs:Y_tr})
            img_input = np.squeeze(X_tr, axis=0)
            img_recon = np.squeeze(img_recon, axis=0)
            img_ground = np.squeeze(Y_tr, axis=0)

            plt.clf()
            plt.rcParams['font.size'] = 100
            plt.figure(figsize=(100, 40))
            plt.subplot(131)
            plt.title("Low-Resolution")
            plt.imshow(img_input)
            plt.subplot(132)
            plt.title("Reconstruction")
            plt.imshow(img_recon)
            plt.subplot(133)
            plt.title("High-Resolution")
            plt.imshow(img_ground)
            plt.tight_layout(pad=1, w_pad=1, h_pad=1)
            plt.savefig("%s/training/%d_psnr_%d.png" %(PACK_PATH, it, int(tmp_psnr)))
            plt.close()

            """static img(test)"""
            X_tr, Y_tr = dataset.next_batch(idx=int(0))
            img_recon, tmp_psnr = sess.run([neuralnet.recon, neuralnet.psnr], feed_dict={neuralnet.inputs:X_tr, neuralnet.outputs:Y_tr})
            list_psnr_te.append(tmp_psnr)
            img_recon = np.squeeze(img_recon, axis=0)
            plt.imsave("%s/static/reconstruction/%d_psnr_%d.png" %(PACK_PATH, it, int(tmp_psnr)), img_recon)

            if(it % 100 == 0):
                img_input = np.squeeze(X_tr, axis=0)
                img_ground = np.squeeze(Y_tr, axis=0)
                plt.imsave("%s/static/bicubic/%d.png" %(PACK_PATH, it), img_input)
                plt.imsave("%s/static/high-resolution/%d.png" %(PACK_PATH, it), img_ground)

        print("Iteration [%d / %d] | Loss: %f  PSNR: %f" %(it, iteration, loss_tr, psnr_tr))

        saver.save(sess, PACK_PATH+"/Checkpoint/model_checker")

    print("Final iteration | Loss: %f  PSNR: %f" %(loss_tr, psnr_tr))

    elapsed_time = time.time() - start_time
    print("Elapsed: "+str(elapsed_time))

    np.save("loss", np.asarray(list_loss))
    plt.clf()
    plt.rcParams['font.size'] = 15
    plt.plot(list_loss, color='blue', linestyle="-", label="loss")
    plt.ylabel("L2 loss")
    plt.xlabel("Iteration")
    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
    plt.savefig("loss.png")
    plt.close()

    np.save("psnr", np.asarray(list_psnr))
    plt.clf()
    plt.rcParams['font.size'] = 15
    plt.plot(list_psnr, color='blue', linestyle="-", label="loss")
    plt.ylabel("PSNR (db)")
    plt.xlabel("Iteration")
    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
    plt.savefig("psnr.png")
    plt.close()

    np.save("psnr_te_static", np.asarray(list_psnr_te))
    plt.clf()
    plt.rcParams['font.size'] = 15
    plt.plot(list_psnr_te, color='blue', linestyle="-", label="loss")
    plt.ylabel("PSNR (db)")
    plt.xlabel("Iteration")
    plt.tight_layout(pad=1, w_pad=1, h_pad=1)
    plt.savefig("psnr_te_static.png")
    plt.close()

def validation(sess, neuralnet, saver, dataset):

    if(os.path.exists(PACK_PATH+"/Checkpoint/model_checker.index")):
        saver.restore(sess, PACK_PATH+"/Checkpoint/model_checker")

    makedir(PACK_PATH+"/test")
    makedir(PACK_PATH+"/test/bicubic")
    makedir(PACK_PATH+"/test/reconstruction")
    makedir(PACK_PATH+"/test/high-resolution")

    start_time = time.time()
    print("\nValidation")
    for tidx in range(dataset.amount_te):

        X_te, Y_te = dataset.next_batch(idx=int(tidx))
        img_recon, tmp_psnr = sess.run([neuralnet.recon, neuralnet.psnr], feed_dict={neuralnet.inputs:X_te, neuralnet.outputs:Y_te})
        img_recon = np.squeeze(img_recon, axis=0)
        plt.imsave("%s/test/reconstruction/%d_psnr_%d.png" %(PACK_PATH, tidx, int(tmp_psnr)), img_recon)

        img_input = np.squeeze(X_te, axis=0)
        img_ground = np.squeeze(Y_te, axis=0)
        plt.imsave("%s/test/bicubic/%d.png" %(PACK_PATH, tidx), img_input)
        plt.imsave("%s/test/high-resolution/%d.png" %(PACK_PATH, tidx), img_ground)

    elapsed_time = time.time() - start_time
    print("Elapsed: "+str(elapsed_time))
